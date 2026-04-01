from slinn import ApiDispatcher, ProjectAPI, AsyncRequest, HttpResponse
import geety as G
import json


dp = ApiDispatcher()
gapp = G.App(context={
    'PNAME': ProjectAPI.get_config()['name']
})

# Write your code down here
storages = {
    'palletes': [],
    'themes': [],
}
for plugin in ProjectAPI.get_plugins():
    storage = ProjectAPI.get_plugin_storage(plugin)
    for key in storages:
        if storage.isdir(key):
            storages[key].append(storage.substorage(key))


def reload_components():
    gapp.components = {}
    palletes_json = {}
    for palletes in storages['palletes']:
        with palletes('palletes.json', 'r') as palletes_json_f:
            palletes_json = json.loads(palletes_json_f.read())
        for pallete in palletes_json['palletes']:
            if palletes.isdir(pallete['path']):
                for components_fn in palletes.listdir(pallete['path']):
                    if components_fn.endswith('.xml'):
                        with palletes(pallete['path'] + '/' + components_fn, 'r') as components:
                            gapp.load(components)


@dp.get('screenshoter')
async def index(request: AsyncRequest):
    reload_components()
    page = G.page.Page(gapp.components | {
        'View': G.component.Component(
            tag = 'View',
            parent = G.component.Component( tag = 'Geety' ),
            children = [
                G.component.Component(
                    tag = key,
                    args = {
                        'id': key,
                        'class': '_FSU-target'
                    }
                )
                for key in gapp.components
            ],
            _is_def = True
        )
    }, [])
    page.set_entry_point('View')
    await request.respond(HttpResponse, await page.html(), content_type='text/html; charset=utf-8')
