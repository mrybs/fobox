class Trash {
    constructor (element, canvas) {
        this.element = element
        this.canvas = canvas
        
        this.element.ondragover = (event) => {
            event.preventDefault();
        }
        this.element.ondrop = (event) => {
            event.preventDefault()
            let component = this.canvas.getComponentById(event.dataTransfer.getData('plain/text'))
            if (!component.isInPalletes()){
                component.remove()
            }
        }
    }
}
