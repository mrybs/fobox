from __future__ import annotations
from typing import Optional
from collections.abc import Generator
from itertools import chain
from urllib.parse import quote
from . import exceptions
from .utils import list_strip, merge_dicts, get_nested_value
import html
import re
import orm


VAR_PATTERN = re.compile(r'\$([\w\.]+)(@html|@url)?')
INSTRUCTION_PATTERN = re.compile(r'^\{(Geety|DB@[0-9]+)\}[\w\.]+$')
DB_QUERY_PATTERN = re.compile(r'^\{DB@[0-9]+\}Query$')
DB_OP_PATTERN = re.compile(r'^\{DB@([0-9]+)\}([\w\.]+)$')


async def var_pattern_apply_content(content, context, page, prevs):
    context = context.copy()
    pp_context = {}
    for var, _ in VAR_PATTERN.findall(content):
        if '.' in var:
            context[var] = get_nested_value(context[var.split('.')[0]], '.'.join(var.split('.')[1:]))
        if issubclass(type(context.get(var)), Component):
            pp_context[var] = await context[var].render(page, context, prevs)
        else:
            pp_context[var] = str(context[var])

    def replacer(match):
        var = match.group(1)
        if match.group(2) == '@html':
            return html.escape(pp_context[var])
        elif match.group(2) == '@url':
            return quote(pp_context[var])
        else:
            return pp_context[var]
    
    return VAR_PATTERN.sub(replacer, content)


async def var_pattern_apply_args(args, context, page, prevs):
    return {
        key: eval(await var_pattern_apply_content(val, context, page, prevs))
        for key, val in args.items()
    }


async def cond_exec(condition, context, page, prevs):
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
    return eval(await var_pattern_apply_content(condition, new_context, page, prevs))


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
    
    async def render(self, page: 'Page', context: dict, prevs: list[Component] | None = None) -> str:
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
                context.update(await var_pattern_apply_args(component.args, context, page, prevs+[self]))
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
                                html += await var_pattern_apply_content(subchild, context, page, prevs+[self])
                            else:
                                subchild = subchild.copy()
                                html += await subchild.render(page, context, prevs+[self])
            case '{Geety}If':
                if await cond_exec(self.args.get('cond', 'False'), context, page, prevs):
                    for child in self:
                        if type(child) is str:
                            html += await var_pattern_apply_content(child, context, page, prevs+[self])
                        else:
                            html += await child.render(page, context, prevs+[self])
            case '{Geety}Switch':
                for case in self.find_all_by_tag('{Geety}Case'):
                    if await cond_exec(case.args.get('cond', 'False'), context, page, prevs):
                        for child in case:
                            if type(child) is str:
                                html += await var_pattern_apply_content(child, context, page, prevs+[self])
                            else:
                                html += await child.render(page, context, prevs+[self])
            case '{Geety}Page':
                if 'title' in self.args:
                    page.set_title(self.args['title'])
                if 'favicon' in self.args:
                    page.set_favicon(self.args['favicon'])
            case 'style':
                style = ''
                for child in self:
                    if type(child) is str:
                        style += await var_pattern_apply_content(child, context, page, prevs+[self])
                    else:
                        style += await child.render(page, context, prevs+[self])
                page.add_style(style)
            case tag if DB_QUERY_PATTERN.fullmatch(tag):
                cont_index = int(DB_OP_PATTERN.findall(tag)[0][0])
                query_id = self.args.get('id')
                async with await page.db_pools[cont_index-1].acquire() as conn:
                    if 'collection' not in self.args:
                        raise exceptions.DBCollectionNotSpecified(cont_index)
                    collection: orm.CollectionProtocol = getattr(conn, self.args['collection'])
                    result = []
                    if query_id is not None:
                        context[query_id] = result
                    for command in self:
                        if type(command) is str:
                            continue
                        op_index, op_name = DB_OP_PATTERN.findall(command.tag)[0]
                        op_index = int(op_index)
                        if cont_index != op_index:
                            raise exceptions.DBContextMismatch(cont_index, op_index, op_name)
                        op_args = await var_pattern_apply_args(command.args, context, page, prevs+[self])
                        match op_name:
                            case 'Find':
                                result += await collection.find(
                                    op_args.get('filter', {}),
                                    fields=[
                                        field.strip() for field in 
                                        command.args.get('fields', '*').split(',')
                                    ]
                                )
                            case 'Insert':
                                result += await collection.insert(
                                    op_args.get('values', {}),
                                    returning=[
                                        field.strip() for field in 
                                        op_args.get('returning', '').split(',')
                                    ]
                                )
                            case 'Count':
                                result.append(await collection.count(
                                    op_args.get('filter', {})
                                ))
                            case 'Delete':
                                await collection.delete(
                                    op_args.get('filter', {})
                                )
                            case 'Update':
                                result += await collection.update(
                                    op_args.get('filter', {}),
                                    op_args.get('values', {}),
                                    returning=[
                                        field.strip() for field in 
                                        op_args.get('returning', '').split(',')
                                        if field.strip()
                                    ]
                                )
                            case 'Pop':
                                result += await collection.pop(
                                    op_args.get('filter', {}),
                                    returning=[
                                        field.strip() for field in 
                                        op_args.get('returning', '').split(',')
                                        if field.strip()
                                    ]
                                )
            case '{Geety}Arg': ...  # skip
            case _:
                signature = {
                    arg.args['name']: arg.args.get('def')
                    for arg in component.find_all_by_tag('{Geety}Arg')
                }
                if component.is_def():
                    merge_dicts(signature, await var_pattern_apply_args(self.args, context, page, prevs+[self]))
                    merge_dicts(context, signature)
                component.args = await var_pattern_apply_args(component.args, context, page, prevs+[self])
                context.update(component.args)
                html += f'<{tag} {' '.join([f"{key}=\"{val}\"" for key, val in component.args.items()])}>' if not self.is_def() else ''
                if self.tag not in page.components or self.is_def():
                    for child in self:
                        if type(child) is str:
                            html += await var_pattern_apply_content(child, context, page, prevs+[self])
                        else:
                            html += await child.render(page, context, prevs+[self])
                elif self.tag in page.components and not self.is_def():
                    html += await page.components[self.tag].copy().render(page, context, prevs+[RenderedComponent.from_component(
                        ''.join([
                                subchild if type(subchild) is str else await subchild.render(page, context, prevs)
                                for subchild in self
                        ]), self
                    )])
        html += f'</{tag}>' if not INSTRUCTION_PATTERN.findall(tag) and not self.is_def() else ''
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
