from __future__ import annotations
from . import exceptions
from .component import Component
from .mime_types import MIME_TYPES
import orm
import html


class Page:
    def __init__(self, components: dict, db_pools: list[orm.PoolProtocol], *, context: dict | None = None):
        self.components = components
        self.db_pools = db_pools
        self.entry_point = None
        self.styles = []
        self.locale = 'ru_RU'
        self.title = 'Geety Page'
        self.favicon = None
        self.viewport = 'width=device-width, initial-scale=1'
        self.robots = ''
        self.description = ''
        self.keywords = ''
        self.author = ''
        self.canonical = ''
        self.image = ''
        self.type = 'website'
        self.card = 'summary'
        self.base_href = None
        self.base_target = '_self'
        self.links = []
        self.context = context or {}
        self.meta = [
            { 'charset': 'UTF-8' }
        ]
    
    def set_entry_point(self,
                        entry_point: str | Component) -> None:
        self.entry_point = self.components[entry_point] if issubclass(type(entry_point), str) else entry_point
    
    def add_style(self, style: str) -> None:
        self.styles.append(style)
    
    def add_link(self, link_args: dict) -> None:
        self.links.append(link_args)
    
    def add_meta(
        self,
        *, 
        name: str | None = None,
        property: str | None = None,
        content: str | None = None) -> None:
        self.meta.append(
            ({ 'name': name } if name else {}) |
            ({ 'property': property } if property else {}) |
            ({ 'content': content } if content else {})
        )
    
    def set_title(self, title: str) -> None:
        self.title = title
    
    def set_favicon(self, favicon: str) -> None:
        self.favicon = favicon
    
    def set_base_href(self, base_href: str) -> None:
        self.base_href = base_href
    
    def set_base_target(self, base_target: str) -> None:
        self.base_target = base_target
    
    def set_viewport(self, viewport: str) -> None:
        self.viewport = viewport
    
    def set_robots(self, robots: str) -> None:
        self.robots = robots
    
    def set_description(self, description: str) -> None:
        self.description = description
    
    def set_keywords(self, keywords: str) -> None:
        self.keywords = keywords
    
    def set_author(self, author: str) -> None:
        self.author = author
    
    def set_canonical(self, canonical: str) -> None:
        self.canonical = canonical
    
    def set_image(self, image: str) -> None:
        self.image = image
    
    def set_type(self, _type: str) -> None:
        self.type = _type
    
    def set_locale(self, locale: str) -> None:
        self.locale = locale
    
    def set_card(self, card: str) -> None:
        self.card = card
                        
    async def html(self,
             *,
             component: Component | None = None,
             context: dict | None = None) -> str:
        if not self.entry_point:
            raise exceptions.EntryPointNotSet()

        body = await (component or self.entry_point).render(self, self.context|(context or {}))

        base = (
            '<base '
            f'target="{self.base_target}"'
            f'{'' if self.base_href is None else f'href="{self.base_href}"'}>'
        )

        if self.description:
            self.add_meta(name='description', content=self.description)
            self.add_meta(property='og:description', content=self.description)
            self.add_meta(name='twitter:description', content=self.description)
        if self.image:
            self.add_meta(property='og:image', content=self.image)
            self.add_meta(name='twitter:image', content=self.image)
        if self.type:
            self.add_meta(property='og:type', content=self.type)
        if self.card:
            self.add_meta(name='twitter:card', content=self.card)
        if self.favicon:
            self.add_link(
                { 'rel': 'icon', 'href': self.favicon } | 
                ({ 'type': MIME_TYPES[self.favicon.split('.')[-1]] }
                    if self.favicon.split('.')[-1] in MIME_TYPES else {})
            )
        if self.canonical:
            self.add_link({ 'rel': 'canonical', 'href': self.canonical })
        if self.keywords:
            self.add_meta(name='keywords', content=self.keywords)
        if self.author:
            self.add_meta(name='author', content=self.author)
        if self.viewport:
            self.add_meta(name='viewport', content=self.viewport)
        if self.robots:
            self.add_meta(name='robots', content=self.robots)

        meta = ''.join(['<meta ' + ' '.join([
            f'{key}="{html.escape(val)}" '
            for key, val in meta.items()
        ]) + '>' for meta in self.meta])

        links = ''.join(['<link ' + ' '.join([
            f'{key}="{html.escape(val)}" '
            for key, val in link.items()
        ]) + '>' for link in self.links])
    
        return (
            '<!DOCTYPE html>\n'
            f'<html {f'lang="{self.locale.split('_')[0]}"' if self.locale else ''}>'
                '<head>'
                    f'{meta}'
                    f'{base}'
                    f'{links}'
                    f'<title>{self.title}</title>'
                    f'<style>{''.join(self.styles)}</style>'
                '</head>'
                '<body>'
                    f'{body}'
                '</body>'
            '</html>'
        )