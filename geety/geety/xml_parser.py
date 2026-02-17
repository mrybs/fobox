from __future__ import annotations
from typing import Optional
from io import TextIOBase
from xml.etree import ElementTree as ET
from .component import Component


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