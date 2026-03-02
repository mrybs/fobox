class Canvas {
    constructor (element, palletes, properties) {
        this.components = new Map()
        this.palletes = palletes
        this.properties = properties
        this.element = element
        this.backlight_component = null

        this.root_component = this.createComponent(
            'root',
            '',
            '<div class="editor-root-component" style="display:flex;flex-wrap:wrap;align-content:flex-start"></div>',
            '.editor-root-component',
            [
                new Property(PropertyTypes.VARIANTS, 'direction', 'Направление', 
                    (element) => {
                        return (element.style.flexDirection == 'column') ? 'column' : 'row'
                    },
                    (element, value) => {
                        element.style.flexDirection = (value == 'row' ? 'row' : 'column')
                    },
                    {
                        options: new Map([
                            ['row', 'по горизонтали'],
                            ['column', 'по вертикали']
                        ])
                    }
                )
            ]
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
    
    isComponentInPalletesById (id) {
        return this.palletes.map(pallete => { return pallete.component_ids }).flat().includes(id)
    }

    toGeety () {
        let xml = `<?xml version="1.0"?><Geety xmlns:G="Geety" xmlns:F="Fobox"><View>`
        for (let child of this.root_component.children) {
            xml += child.toGeety()
        }
        xml += `</View></Geety>`
        return xml
    }
}