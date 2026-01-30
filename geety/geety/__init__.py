from __future__ import annotations
from typing import Optional
from io import TextIOBase
from collections import namedtuple
from itertools import chain
from xml.etree.ElementTree import XMLPullParser
import re


EntryPoint = namedtuple('EntryPoint', ('path', 'query'))


class App:
    def __init__(self):
        self._loaded ={}
    
    def load(self, name: str, file: TextIOBase) -> None:
        self._loaded[name] = parse_component(file)
    
    def html(self,
             entry_point: EntryPoint | Component = EntryPoint('Card', 'Geety App'),
             *,
             with_headers: bool = True) -> str:
        html = ''
        if with_headers:
            html += '<!DOCTYPE html>'
            html += '<html><head></head><body>'
        
        if issubclass(type(entry_point), EntryPoint):
            entry_point = self._loaded[entry_point.path].query(entry_point.query)
        html += f'<{entry_point.tag}>'

        for child in entry_point.children:
            html += self.html(child, with_headers=False)

        html += entry_point.content
        html += f'</{entry_point.tag}>'

        if with_headers:
            html += '</body></html>'
        return html


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
        if self.tag == tag:
            return self
        for child in self.children:
            if component := child.find_by_tag(tag):
                return component
        return None

    def find_all_by_tag(self, tag: str) -> list[Component]:
        components = []
        if self.tag == tag:
            components.append(self)
        for child in self.children:
            components.extend(child.find_by_tag(tag))
        return components
                    
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