function parseGeetyComponent (component_element, canvas) {
    let name = component_element.getElementsByTagNameNS('Fobox', 'Name')[0].textContent
    for (let _name of component_element.getElementsByTagNameNS('Fobox', 'Name')) _name.remove()

    let properties = new Array()

    for (let fobox_properties of component_element.getElementsByTagNameNS('Fobox', 'Properties')) {
        for (let fobox_property of fobox_properties.getElementsByTagNameNS('Fobox', 'Property')) {
            const type = PropertyTypes[fobox_property.getAttribute('type')]
            const key = fobox_property.getAttribute('key')
            const name = fobox_property.getAttribute('name')
            const onload = eval(fobox_property.getElementsByTagNameNS('Fobox', 'PropertyOnLoad')[0].textContent)
            const onchange = eval(fobox_property.getElementsByTagNameNS('Fobox', 'PropertyOnChange')[0].textContent)
            let args = {}
            if (fobox_property.getElementsByTagNameNS('Fobox', 'PropertyArgs').length) {
                for (let _arg of fobox_property.getElementsByTagNameNS('Fobox', 'PropertyArgs')[0].children) {
                    let arg = null
                    switch (_arg.getAttribute('type')) {
                        case 'map':
                            arg = new Map()
                            for (let value of _arg.getElementsByTagNameNS('Fobox', 'PropertyValue')) {
                                arg.set(value.getAttribute('key'), value.textContent)
                            }
                            break
                        case 'value':
                            arg = _arg.textContent
                            break
                    }
                    args[_arg.getAttribute('name')] = arg
                }
            }
            properties.push(new Property(type, key, name, onload, onchange, args))
        }
    }
    for (let _fobox_properties of component_element.getElementsByTagNameNS('Fobox', 'Properties')) _fobox_properties.remove()

    let container = false

    if (component_element.getElementsByTagNameNS('Geety', 'Content').length) {
        let elementPath = generateElementPathPrefix()
        let container_element = component_element.getElementsByTagNameNS('Geety', 'Content')[0].parentElement
        container_element.classList.add(elementPath)
        container = '.' + elementPath
    }
    for (let _content of component_element.getElementsByTagNameNS('Geety', 'Content')) _content.remove()
    let tag = component_element.hasAttributeNS('Geety', 'Extends') ? component_element.getAttributeNS('Geety', 'Extends') : 'div'
    _component_element = document.createElement(tag)
    _component_element.innerHTML = component_element.innerHTML
    for (const attr of component_element.attributes) {
        _component_element.setAttribute(attr.name, attr.value);
    }
    return canvas.createComponent(name, component_element.tagName, _component_element.outerHTML, container, properties)
}

function parseGeety (xml, canvas) {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xml, 'text/xml')
    const root = xmlDoc.getElementsByTagName('Geety')[0]
    let components = []
    for (let component_element of root.children) {
        components.push(parseGeetyComponent(component_element, canvas))
    }
    return components
}
