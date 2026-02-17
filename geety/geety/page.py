from __future__ import annotations
from io import TextIOBase
from . import exceptions
from .component import Component
from .xml_parser import parse_component
from .mime_types import MIME_TYPES
import orm


class Page:
    def __init__(self):
        self.components = {}
        self.entry_point = None
        self.styles = []
        self.db_pools = []
        self.title = 'Geety Page'
        self.favicon = None
    
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
    
    def add_database_pool(self, pool: orm.PoolProtocol):
        self.db_pools.append(pool)
    
    def add_style(self, style):
        self.styles.append(style)
    
    def set_title(self, title):
        self.title = title
    
    def set_favicon(self, favicon):
        self.favicon = favicon
                        
    async def html(self,
             *,
             component: Component | None = None,
             context: dict | None = None) -> str:
        if not self.entry_point:
            raise exceptions.EntryPointNotSet()

        body = await (component or self.entry_point).render(self, context or {})

        favicon = (
            '<link '
            'rel="icon" '
            f'type="{MIME_TYPES.get(self.favicon.split('.')[-1])}" '
            f'href="{self.favicon}">'
        ) if self.favicon else ''
    
        return (
            '<!DOCTYPE html>\n'
            '<html>'
                '<head>'
                    '<meta charset="UTF-8"/>'
                    f'<title>{self.title}</title>'
                    f'{favicon}'
                    f'<style>{''.join(self.styles)}</style>'
                '</head>'
                '<body>'
                    f'{body}'
                '</body>'
            '</html>'
        )