let properties = new Properties(document.getElementById('properties'))
let canvas = new Canvas(document.getElementById('canvas'), [], properties)
let trash = new Trash(document.getElementById('trash'), canvas)

properties.display(canvas.root_component)
canvas.root_component.container_element.appendChild(document.getElementsByClassName('editor-info-h2')[0])

async function loadPalletes () {
    const palletes = (await G.GET_JSON(`/fobox/palletes`)).palletes
    let palletes_element = document.getElementById('palletes')
    for (let pallete_meta of palletes) {
        let pallete_element = document.createElement('div')
        pallete_element.id = `_EditorPallete-${pallete_meta.name}`
        palletes_element.appendChild(pallete_element)
    }
    palletes.forEach(async pallete_meta => {
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
    })
}

async function saveView () {
    let xml = canvas.toGeety()
    r = await G.POST('/fobox/saveView', {}, xml)
    alert(r.status === 200 ? 'Страница успешно сохранена' : 'Произошла ошибка при сохранении')
}

loadPalletes()

addButtonToHeader('Сохранить страницу', saveView)