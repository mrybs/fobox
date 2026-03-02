class Pallete {
    constructor (element) {
        this.element = element
        this.component_ids = []
    }
    
    addComponent (component) {
        this.component_ids.push(component.element.id)
        this.element.appendChild(component.element)
    }
    
    addComponents (components) {
        components.forEach(component => 
            this.addComponent(component)
        )
    }
}