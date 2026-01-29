from __future__ import annotations
from xml.etree.ElementTree import XMLPullParser


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
                    
    def __repr__(self):
        return f'<Component {self.tag} [{", ".join([f"{key}={val}" for key, val in self.args.items()])}] with {len(self.children)} children "{self.content}">'


def parse_component(file):
    parser = XMLPullParser(['start', 'end'])
    stack = []
    for line in file:
        parser.feed(line)
        for event, elem in parser.read_events():
            if event == 'start':
                stack.append(Component(
                    tag=elem.tag,
                    args=elem.attrib,
                    content=elem.text or ''
                ))
            elif event == 'end' and len(stack) > 1:
                stack[-2].children.append(stack[-1])
                del stack[-1]
    return stack[0]


def print_tree(component, lvl=0):
    print(f'{"\t"*lvl}{component}')
    for child in component.children:
        print_tree(child, lvl+1)