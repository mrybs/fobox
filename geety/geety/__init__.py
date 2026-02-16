from __future__ import annotations
from typing import Optional
from io import TextIOBase
from collections.abc import Generator
from itertools import chain
from xml.etree import ElementTree as ET
from urllib.parse import quote
from . import exceptions
import re
import html


VAR_PATTERN = re.compile(r'\$([\w\.]+)(@html|@url)?')
INSTRUCTIONS = ('{Geety}Arg', '{Geety}Set', '{Geety}For', '{Geety}Content', '{Geety}Switch', '{Geety}If')


def var_pattern_apply_content(content, context, page, prevs):
    def replacer(match):
        var = match.group(1)
        val = None
        if issubclass(type(context.get(var)), Component):
            val = context[var].render(page, context, prevs)
        else:
            val = str(context[var])
        if match.group(2) == '@html':
            return html.escape(val)
        elif match.group(2) == '@url':
            return quote(val)
        else:
            return val
    
    return VAR_PATTERN.sub(replacer, content)


def var_pattern_apply_args(args, context, page, prevs):
    return {
        key: eval(var_pattern_apply_content(val, context, page, prevs))
        for key, val in args.items()
    }


def list_strip(lst):
    if not lst:
        return []

    start = 0
    while start < len(lst) and type(lst[start]) is str and lst[start].isspace():
        start += 1
    
    end = len(lst) - 1
    while end >= 0 and type(lst[end]) is str and lst[end].isspace():
        end -= 1
    
    return lst[start : end + 1] if end >= start else []


def merge_dicts(sec, pri):
    for key, value in pri.items():
        if value is None and key in sec:
            continue
        sec[key] = value


def cond_exec(condition, context, page, prevs):
    new_context = {}
    for var, _ in VAR_PATTERN.findall(condition):
        if var not in context:
            return False
        if issubclass(type(context[var]), Component):
            new_context[var] = context[var].render(page, context, prevs)
        elif issubclass(type(context[var]), str):
            new_context[var] = '\'' + context[var] + '\''
        else:
            new_context[var] = context[var]
    condition = var_pattern_apply_content(condition, new_context, page, prevs)
    return eval(condition)


class Page:
    def __init__(self):
        self.components = {}
        self.entry_point = None
        self.styles = []
    
    def load(self, file: TextIOBase) -> None:
        for child in parse_component(file).find_by_tag('Geety').children:
            if type(child) is str:
                continue
            if child.tag in self.components:
                raise exceptions.ComponentAlreadyExists(child.tag)
            child._is_def = True
            self.components[child.tag] = child
    
    def set_entry_point(self,
                        entry_point: str | Component) -> None:
        self.entry_point = self.components[entry_point] if issubclass(type(entry_point), str) else entry_point
    
    def add_style(self, style):
        self.styles.append(style)
                        
    def html(self,
             *,
             component: Component | None = None,
             with_headers: bool = True,
             context: dict | None = None) -> str:
        if not self.entry_point:
            raise exceptions.EntryPointNotSet()
        
        body = (component or self.entry_point).render(self, context or {})

        if not with_headers:
            return body
    
        return (
            '<!DOCTYPE html>\n'
            '<html>'
            '<head>' \
            '<meta charset="UTF-8"/>'
            f'<style>{''.join(self.styles)}</style>'
            '</head>'
            '<body>'
            f'{body}'
            '</body></html>'
        )


class Component:
    def __init__(
            self,
            *,
            tag: str = '',
            args: dict | None = None,
            children: list[Component] | None = None,
            parent: Component | None = None,
            _is_def: bool = False):
        self.tag = tag
        self.args = args or {}
        self.children = list_strip(children or [])
        self.parent = parent
        self._is_def = _is_def
    
    def copy(self) -> Component:
        return Component(
            tag=self.tag,
            args=self.args.copy(),
            children=[
                child if type(child) is str else child.copy()
                for child in self.children
            ],
            parent=self.parent,
            _is_def=self._is_def
        )
    
    def render(self, page: Page, context: dict, prevs: list[Component] | None = None) -> str:
        def find_prev(prevs):
            for i in range(1, len(prevs) - 1):
                if prevs[-i].is_def():
                    return prevs[-i-1]
            return None
        
        prevs = prevs or []
        component = page.components.get(self.tag, self).copy()
        tag = component.args.get('{Geety}Extends', 'div') if self.tag in page.components else self.tag

        html = ''
        match tag:
            case '{Geety}Content':
                prev = find_prev(prevs)
                if type(prev) is RenderedComponent:
                    html += prev.html
            case '{Geety}Set':
                context.update(var_pattern_apply_args(component.args, context, page, prevs+[self]))
            case '{Geety}For':
                element_name, iterable_name = component.args['each'].split(':')
                if iterable_name == 'Content':
                    prev = find_prev(prevs)
                    if type(prev) is RenderedComponent:
                        html += prev.html
                else:
                    for elem in context[iterable_name]:
                        context[element_name] = elem
                        for subchild in component:
                            if type(subchild) is str:
                                html += var_pattern_apply_content(subchild, context, page, prevs+[self])
                            else:
                                subchild = subchild.copy()
                                html += subchild.render(page, context, prevs+[self])
            case '{Geety}If':
                if cond_exec(self.args.get('cond', 'False'), context, page, prevs):
                    for child in self:
                        if type(child) is str:
                            html += var_pattern_apply_content(child, context, page, prevs+[self])
                        else:
                            html += child.render(page, context, prevs+[self])
            case '{Geety}Switch':
                for case in self.find_all_by_tag('{Geety}Case'):
                    if cond_exec(case.args.get('cond', 'False'), context, page, prevs):
                        for child in case:
                            if type(child) is str:
                                html += var_pattern_apply_content(child, context, page, prevs+[self])
                            else:
                                html += child.render(page, context, prevs+[self])
            case 'style':
                style = ''
                for child in self:
                    if type(child) is str:
                        style += var_pattern_apply_content(child, context, page, prevs+[self])
                    else:
                        style += child.render(page, context, prevs+[self])
                page.add_style(style)
            case '{Geety}Arg': ...  # skip
            case _:
                signature = {
                    arg.args['name']: arg.args.get('def')
                    for arg in component.find_all_by_tag('{Geety}Arg')
                }
                if component.is_def():
                    merge_dicts(signature, var_pattern_apply_args(self.args, context, page, prevs+[self]))
                    merge_dicts(context, signature)
                component.args = var_pattern_apply_args(component.args, context, page, prevs+[self])
                context.update(component.args)
                html += f'<{tag} {' '.join([f"{key}=\"{val}\"" for key, val in component.args.items()])}>' if not self.is_def() else ''
                if self.tag not in page.components or self.is_def():
                    for child in self:
                        if type(child) is str:
                            html += var_pattern_apply_content(child, context, page, prevs+[self])
                        else:
                            html += child.render(page, context, prevs+[self])
                elif self.tag in page.components and not self.is_def():
                    html += page.components[self.tag].copy().render(page, context, prevs+[RenderedComponent.from_component(
                        ''.join([
                                subchild if type(subchild) is str else subchild.render(page, context, prevs)
                                for subchild in self
                        ]), self
                    )])
        html += f'</{tag}>' if tag not in INSTRUCTIONS and not self.is_def() else ''
        return html
    
    def query(self, query):
        # TODO: add all type of queries (for tags ' ', for classes '.', for ids '#', for children '>')
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
            if type(child) is not str:
                yield from child.find_all_by_tag(tag)
    
    def is_def(self):
        #return self.parent and not self.parent.parent
        return self._is_def
                    
    def __repr__(self) -> str:
        return f'<Component {'definition' if self.is_def() else ''} {self.tag} [{", ".join([f"{key}={val}" for key, val in self.args.items()])}] with {len(self.children)} children>'

    def __iter__(self) -> Generator[Component]:
        yield from self.children


class RenderedComponent(Component):
    def __init__(
            self,
            html: str,
            *,
            tag: str = '',
            args: dict | None = None,
            children: list[Component] | None = None,
            parent: Component | None = None,
            _is_def: bool = False):
        Component.__init__(
            self,
            tag=tag,
            args=args,
            children=children,
            parent=parent,
            _is_def=_is_def
        )
        self.html = html

    def copy(self) -> Component:
        return Component(
            tag=self.tag,
            args=self.args.copy(),
            children=[
                child if type(child) is str else child.copy()
                for child in self.children
            ],
            parent=self.parent,
            _is_def=self._is_def
        )

    def render(self, components: dict, context: dict, prevs: list[Component], meta: dict) -> str:
        return self.html

    @staticmethod
    def from_component(html: str, component: Component) -> RenderedComponent:
        component = component.copy()
        return RenderedComponent(
            html,
            tag=component.tag,
            args=component.args,
            children=component.children,
            parent=component.parent,
            _is_def=component._is_def
        )
    


def parse_component(file: TextIOBase) -> Optional[Component]:
    # TODO: rewrite with ET.XMLPoolParser 
    def _elem_to_comp(elem: ET.Element, parent: Component | None = None) -> Component:
        comp = Component(tag=elem.tag, args=elem.attrib.copy(), parent=parent)
        if elem.text:
            comp.children.append(elem.text)
        for child in elem:
            comp.children.append(_elem_to_comp(child, parent=comp))
            if child.tail:
                comp.children.append(child.tail)
        return comp
    
    content = file.read()
    return _elem_to_comp(ET.fromstring(content)) if content else None


def print_tree(component, lvl=0) -> None:
    print(f'{"\t"*lvl}{component}')
    for child in component.children:
        print_tree(child, lvl+1)
