from __future__ import annotations
from io import TextIOBase
from typing import Iterable
from . import exceptions
from .xml_parser import parse_component
from .page import Page
import orm


class App:
    def __init__(self, *, context: dict | None):
        self.db_pools = []
        self.components = {}
        self.context = context or {}
    
    @staticmethod
    def _load_file(file: TextIOBase, components_list: Iterable[str]) -> None:
        components = {}
        for child in parse_component(file).find_by_tag('Geety').children:
            if type(child) is str:
                continue
            if child.tag in components_list:
                raise exceptions.ComponentAlreadyExists(child.tag)
            child._is_def = True
            components[child.tag] = child
        return components
    
    def load(self, file: TextIOBase) -> None:
        self.components.update(App._load_file(file, self.components.keys()))
    
    def add_database_pool(self, pool: orm.PoolProtocol):
        self.db_pools.append(pool)

    def new_page(self, page_file):
        return Page(self.components | App._load_file(page_file, self.components.keys()), self.db_pools, context=self.context)
