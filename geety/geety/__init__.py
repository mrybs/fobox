from __future__ import annotations
from typing import Optional
from io import TextIOBase
from collections.abc import Generator
from itertools import chain
from xml.etree.ElementTree import XMLPullParser
from . import exceptions
import re


VAR_PATTERN = re.compile(r'\$([\w\.]+)')


def var_pattern_apply_content(content, context):
    return VAR_PATTERN.sub(lambda m: str(context.get(m.group(1), m.group(0))), content)


def var_pattern_apply_args(args, context):
    return {
        key: eval(var_pattern_apply_content(val, context))
        for key, val in args.items()
    }


class Page:
    def __init__(self):
        self._components = {}
        self.entry_point = None
    
    def load(self, file: TextIOBase) -> None:
        for child in parse_component(file).find_by_tag('Geety').children:
            if child.tag in self._components:
                raise exceptions.ComponentAlreadyExists(child.tag)
            self._components[child.tag] = child
    
    def set_entry_point(self,
                        entry_point: str | Component) -> None:
        self.entry_point = self._components[entry_point] if issubclass(type(entry_point), str) else entry_point
                        
    def html(self,
             *,
             component: Component | None = None,
             with_headers: bool = True,
             context: dict | None = None) -> str:
        if not self.entry_point:
            raise exceptions.EntryPointNotSet()
        
        body = (component or self.entry_point).render(self._components, context or {})

        if not with_headers:
            return body
    
        return (
            '<!DOCTYPE html>\n'
            '<html><head></head><body>'
            f'{body}'
            '</body></html>'
        )


class Component:
    def __init__(
            self,
            *,
            tag: str = '',
            args: dict = None,
            children: list[Component] = None,
            content: str = ''):
        self.tag = tag
        self.args = args or {}
        self.children = children or []
        self.content = content
    
    def copy(self) -> Component:
        return Component(
            tag=self.tag,
            args=self.args.copy(),
            children=[child.copy() for child in self.children],
            content=self.content
        )
    
    def render(self, components: dict, context: dict):
        if self.tag in components:
            signature = {}
            component = components[self.tag]
            parent_tag = component.args.get('{Geety}extends', 'div')
            html = f'<{parent_tag} {' '.join([f"{key}=\"{val}\"" for key, val in component.args.items()])}>'
            for child in component.children:
                child = child.copy()
                if child.tag == '{Geety}arg':
                    signature[child.args['name']] = child.args.get('def')
                    context.update(signature | self.args)
                elif child.tag == '{Geety}Set':
                    child.args = var_pattern_apply_args(child.args, context)
                    context.update(child.args)
                elif child.tag == '{Geety}For':
                    element_name, iterable_name = child.args['each'].split(':')
                    for elem in context[iterable_name]:
                        for subchild in child.children:
                            subchild = subchild.copy()
                            context[element_name] = elem
                            subchild.args = var_pattern_apply_args(subchild.args, context)
                            html += subchild.render(components, context.copy())
                else:
                    child.args = var_pattern_apply_args(child.args, context)
                    child.content = var_pattern_apply_content(child.content, context)
                    html += child.render(components, context.copy())
            html += component.content
            html += f'</{parent_tag}>'
            return html
        else:
            html = f'<{self.tag} {' '.join([f"{key}=\"{val}\"" for key, val in self.args.items()])}>'
            for child in self.children:
                html += child.render(components, {})
            html += self.content
            html += f'</{self.tag}>'
            return html
    
    def query(self, query):
        spl = list(filter(str, re.split(r'([>\.# ])', query)))
        print(spl)
        if len(spl) % 2 == 1:
            spl = [' '] + spl
        it = iter(spl)
        subqueries = list(zip(it, it))
        match subqueries[0][0]:
            case ' ':
                component = self.find_by_tag(subqueries[0][1])
                if len(subqueries) > 1:
                    return component.query(''.join(chain.from_iterable(subqueries[1:])))
                return component
    
    def find_by_tag(self, tag: str) -> Optional[Component]:
        return next(self.find_all_by_tag(tag), None)

    def find_all_by_tag(self, tag: str) -> Generator[Component]:
        if self.tag == tag:
            yield self
        for child in self.children:
            yield from child.find_all_by_tag(tag)
                    
    def __repr__(self) -> str:
        return f'<Component {self.tag} [{", ".join([f"{key}={val}" for key, val in self.args.items()])}] with {len(self.children)} children "{self.content}">'


def parse_component(file: TextIOBase) -> Optional[Component]:
    parser = XMLPullParser(['start', 'end'])
    stack = []
    for line in file:
        parser.feed(line)
        for event, elem in parser.read_events():
            if event == 'start':
                stack.append(Component(
                    tag=elem.tag,
                    args=elem.attrib.copy()
                ))
            elif event == 'end' and len(stack) > 1:
                stack[-1].content = elem.text or ''
                stack[-2].children.append(stack[-1])
                del stack[-1]
    return stack[0] if stack else None


def print_tree(component, lvl=0) -> None:
    print(f'{"\t"*lvl}{component}')
    for child in component.children:
        print_tree(child, lvl+1)
