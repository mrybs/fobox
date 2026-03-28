class Canvas {
    constructor (element, palletes, properties) {
        this.components = new Map()
        this.palletes = palletes
        this.properties = properties
        this.element = element
        this.backlight_component = null

        this.root_component = this.createComponent(
            'Страница',
            'View',
            '<div class="editor-root-component" style="display:flex;flex-wrap:wrap;align-content:flex-start"></div>',
            '.editor-root-component',
            []
        )
        this.root_component.element.setAttribute('draggable', false)
        this.element.appendChild(this.root_component.element)
    }

    createComponent (name, gtag, innerHTML, container=false, properties=new Array()) {
        return new Component(name, gtag, innerHTML, this, container, null, new Array(), properties)
    }
    
    getComponentById (id) {
        return this.components.get(id)
    }

    getComponentInPalletesByGtag (gtag) {
        for (let component_id of this.palletes.map(pallete => { return pallete.component_ids }).flat()) {
            let component = this.getComponentById(component_id)
            if (component.gtag === gtag) return component
        }
    }
    
    isComponentInPalletesById (id) {
        return this.palletes.map(pallete => { return pallete.component_ids }).flat().includes(id)
    }

    toGeety () {
        let xml = `<?xml version="1.0"?><Geety xmlns:G="Geety" xmlns:F="Fobox">`
        xml += this.root_component.toGeety()
        xml += `</Geety>`
        return xml
    }
}