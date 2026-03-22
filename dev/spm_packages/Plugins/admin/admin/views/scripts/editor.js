const VIEW = window.location.pathname.split('/').pop()

let properties = new Properties(document.getElementById('properties'))
let canvas = new Canvas(document.getElementById('canvas'), [], properties)
let trash = new Trash(document.getElementById('trash'), canvas)


async function loadPalletes () {
    const palletes = (await G.GET_JSON(`/fobox/palletes`)).palletes
    let palletes_element = document.getElementById('palletes')
    for (let pallete_meta of palletes) {
        let pallete_element = document.createElement('div')
        pallete_element.id = `_EditorPallete-${pallete_meta.name}`
        palletes_element.appendChild(pallete_element)
    }
    await Promise.all(palletes.map(async pallete_meta => {
        let pallete_element = document.getElementById(`_EditorPallete-${pallete_meta.name}`)
        pallete_element.classList.add('pallete')
        pallete_element.innerHTML += `
            <div>${pallete_meta.name}</div>
        `
        let pallete = new Pallete(pallete_element)
        let pallete_json = await G.GET_JSON(`/fobox/palletes/${pallete_meta.path}`)
        pallete_json.components.forEach(component => {
            pallete.addComponents(parseGeety(component, canvas))
        })
        canvas.palletes.push(pallete)
    }))
}

async function saveView () {
    let xml = canvas.toGeety()
    r = await G.POST(`/fobox/saveView/${VIEW}`, {}, xml)
    alert(r.status === 200 ? 'Страница успешно сохранена' : 'Произошла ошибка при сохранении')
}

async function loadView () {
    let resp = await G.GET(`/fobox/loadView/${VIEW}`)
    if (resp.status !== 200) return
    let xml = await (resp).text()
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xml, 'application/xml')
    const root = xmlDoc.getElementsByTagName('Geety')[0]
    const view = root.getElementsByTagName('View')[0]
    canvas.root_component.clear()
    await loadComponent(view, canvas.root_component)
    if (view.hasAttributeNS('Fobox', 'Properties')){
        canvas.root_component.setProperties(JSON.parse(view.getAttributeNS('Fobox', 'Properties')))
    }
}

async function loadComponent (element, parent) {
    for (let component_element of element.children) {
        let component = canvas.getComponentInPalletesByGtag(component_element.tagName).copy()
        await loadComponent(component_element, component)
        if (component_element.hasAttributeNS('Fobox', 'Properties')){
            component.setProperties(JSON.parse(component_element.getAttributeNS('Fobox', 'Properties')))
        }
        parent.appendChild(component)
    }
}

async function main () {
    properties.display(canvas.root_component)
    canvas.root_component.container_element.appendChild(document.getElementsByClassName('editor-info-h2')[0])
    addButtonToHeader('Сохранить страницу', saveView)
    await loadPalletes()
    await loadView()
}

main()
