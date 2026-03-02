class Properties {
    constructor (element) {
        this.element = element
        this.current_component = null
    }

    display (component) {
        if (this.current_component !== null) {
            this.current_component.element.removeAttribute('properties-opened')
        }
        if (component === null){
            return this.element.replaceChildren()
        }
        component.element.setAttribute('properties-opened', true)
        this.element.innerHTML = `
            <h2>${component.name}</h2>
        `
        component.properties.forEach(property => {
            let property_element = document.createElement('div')
            property_element.classList.add('editor-property')
            property_element.innerHTML = `<span class="editor-property-label">${property.name}</span>`
            let element = component.body.querySelector('*')
            switch (property.type){
                case PropertyTypes.TEXT: {
                    let input = document.createElement('input')
                    input.setAttribute('type', 'text')
                    input.value = property.onload(element)
                    input.oninput = event => { property.onchange(element, event.target.value) }
                    property_element.appendChild(input)
                    break
                }
                case PropertyTypes.COLOR: {
                    let input = document.createElement('input')
                    input.setAttribute('type', 'color')
                    input.value = property.onload(element)
                    input.oninput = event => { property.onchange(element, event.target.value) }
                    property_element.appendChild(input)
                    break
                }
                case PropertyTypes.NUMBER: {
                    let input = document.createElement('input')
                    input.setAttribute('type', 'number')
                    input.setAttribute('min', property.args.min)
                    input.setAttribute('max', property.args.max)
                    input.setAttribute('step', property.args.step)
                    input.value = property.onload(element)
                    input.oninput = event => { property.onchange(element, event.target.value) }
                    property_element.appendChild(input)
                    break
                }
                case PropertyTypes.VARIANTS: {
                    let select = document.createElement('select')
                    property.args.options.forEach((value, key) => {
                        let option_element = document.createElement('option')
                        option_element.setAttribute('value', key)
                        option_element.innerText = value
                        select.appendChild(option_element)
                    })
                    select.value = property.onload(element)
                    select.onchange = event => { property.onchange(element, event.target.value) }
                    property_element.appendChild(select)
                    break
                }
            }
            this.element.appendChild(property_element)
        })
        this.current_component = component
    }
}
