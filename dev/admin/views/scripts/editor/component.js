class Component {
    constructor (name, gtag, innerHTML, canvas, container=false, parent=null, children=new Array(), properties=new Array()) {
        this.name = name
        this.gtag = gtag
        this.container = container
        this.parent = parent
        this.children = children
        this.canvas = canvas
        this.properties = properties
        this.id = generateId()
        this.canvas.components.set(this.id, this)

        this.element = document.createElement('div')
        this.element.id = this.id
        this.element.classList.add('editor-component')
        this.element.setAttribute('draggable', true)

        this.element.innerHTML = `
            <div class="editor-component-header">
                <span class="material-symbols-outlined editor-component-properties-button">page_info</span>
                ${this.name}
            </div>
            <div class="editor-component-content">${innerHTML}</div>
        `
        this.header = this.element.getElementsByClassName('editor-component-header')[0]
        this.propertiesButton = this.header.getElementsByClassName('editor-component-properties-button')[0]
        this.body = this.element.getElementsByClassName('editor-component-content')[0]
        
        this.context_menu_items = new Array()
        this.context_menu_items.push({ label: 'Открыть свойства', icon: 'page_info', color: 'var(--editor-fg)', onclick: ev => {
            this.canvas.properties.display(this)
        }})
        if (this.canvas.root_component !== undefined){
            this.context_menu_items.push({ label: 'Удалить', icon: 'delete', color: 'var(--editor-danger-fg)', onclick: ev => {
                this.remove()
            }})
            this.context_menu_items.push({ label: 'Дублировать', icon: 'content_copy', color: 'var(--fg)', onclick: (ev) => {
                let copy = this.copy()
                console.log(copy)
                this.insertAfter(copy)
            }})
            if (this.container) {
                this.context_menu_items.push({ label: 'Дублировать без содержимого', icon: 'copy_all', color: 'var(--fg)', onclick: ev => {
                    this.canvas.properties.display(this)
                    let copy = this.copy()
                    copy.children = new Array()
                    copy.container_element.replaceChildren()
                    this.insertAfter(copy)
                }})
            }
        }

        this.element.ondragstart = event => {
            event.dataTransfer.setData('plain/text', event.target.id)
        }

        this.body.onclick = this.header.onclick = event => {
            event.stopPropagation()
            hideContextMenu()
            if (this.isInPalletes()) return
            this.canvas.properties.display(this)
        }

        this.body.oncontextmenu = event => {
            console.log(event)
            event.stopPropagation()
            event.preventDefault()
            if (!this.canvas.isComponentInPalletesById(this.id)) {
                showContextMenu(event.clientX, event.clientY, this.context_menu_items)
            }
        }
        
        if (this.container) {
            this.container_element = this.body.querySelector(this.container)
            this.element.ondragover = event => {
                event.preventDefault()
                event.stopPropagation()
                const target_component = this.canvas.getComponentById(getComponentId(event.target))
                const closest = getClosestWithSide(this.container_element, event.clientX, event.clientY);
                if (closest.element && closest.side !== Sides.INSIDE) {
                    this.canvas.getComponentById(getComponentId(closest.element)).setOuterBacklight(closest.side)
                } else {
                    this.setInnerBacklight()
                }
            }
            this.element.ondragleave = event => {
                event.stopPropagation()
                if (this.canvas.backlight_component !== null){
                    this.canvas.backlight_component.setOuterBacklight(null)
                }
            }
            this.element.ondrop = event => {
                event.preventDefault()
                event.stopPropagation()
                if (this.canvas.backlight_component !== null){
                    this.canvas.backlight_component.setOuterBacklight(null)
                }
                if (this.canvas.isComponentInPalletesById(this.id)) return
                const id = event.dataTransfer.getData('plain/text')
                const target_component = this.canvas.getComponentById(getComponentId(event.target))
                const component =   (this.canvas.isComponentInPalletesById(id) ? 
                                    this.canvas.getComponentById(id).copy(target_component) : 
                                    this.canvas.getComponentById(id))
                try {
                    target_component.insertChild(component, event.clientX, event.clientY)
                    this.canvas.properties.display(component)
                } catch (err) {
                    if (err.name !== 'HierarchyRequestError'){
                        throw err
                    }
                }
            }
        }
    }
    
    appendChild (component) {
        if (!this.container) {
            return getContainer(this.canvas, this.element).appendChild(component)
        }
        this.container_element.appendChild(component.element)
        this.children.push(component)
        if (component.parent !== null) {
            component.parent.children.splice(component.parent.children.indexOf(component))
        }
        component.parent = this
    }

    insertAfter (component) {
        this.element.after(component.element)
        if (component.parent && component.parent !== this.parent) {
            component.parent.children = component.parent.children.filter(c => c !== component);
        }
        if (!this.parent.children.includes(component)) {
            this.parent.children.push(component);
        }
        component.parent = this.parent;
    }

    insertChild(component, clientX, clientY) {
        if (!this.container) {
            return getContainer(this.canvas, this.element).insertChild(component, clientX, clientY)
        }
        if (component.parent) {
            component.parent.children = component.parent.children.filter(c => c !== component)
        }
        const closest = getClosestWithSide(this.container_element, clientX, clientY);
        if (closest.element) {
            closest.component = this.canvas.getComponentById(getComponentId(closest.element))
            switch (closest.side){
                case Sides.LEFT:
                case Sides.TOP:
                    this.container_element.insertBefore(component.element, closest.element)
                    this.children.splice(this.children.indexOf(closest.component), 0, component)
                    break
                case Sides.RIGHT:
                case Sides.BOTTOM:
                case Sides.INSIDE:
                    closest.element.after(component.element)
                    this.children.splice(this.children.indexOf(closest.component) + 1, 0, component)
                    break
            }
        } else {
            this.container_element.appendChild(component.element);
            this.children.push(component)
        }
        /*if (component.parent && component.parent !== this) {
            component.parent.children = component.parent.children.filter(c => c !== component);
        }
        if (!this.children.includes(component)) {
            this.children.push(component);
        }*/
        component.parent = this;
    }

    copy(parent = null) {
        const newComponent = new Component(
            this.name,
            this.gtag,
            this.body.innerHTML,
            this.canvas,
            this.container,
            null,
            new Array(),
            this.properties
        );
        if (newComponent.container){
            newComponent.container_element.replaceChildren()
            this.children.forEach(child => {
                const childCopy = child.copy(newComponent);
                newComponent.appendChild(childCopy);
            });
        }
        if (parent) {
            parent.appendChild(newComponent);
        }
        return newComponent;
    }
    
    remove () {
        this.element.remove()
        if (this.parent) {
            this.parent.children.splice(this.parent.children.indexOf(this));
        }
        this.canvas.components.delete(this.id)
        this.canvas.properties.display(this.canvas.root_component)
    }

    isInPalletes () {
        return this.canvas.isComponentInPalletesById(this.id)
    }

    isRoot () {
        if (this.canvas.root_component === null) return true
        if (this.canvas.root_component.id === this.id) return true
        return false
    }

    setOuterBacklight (side) {
        if (this.isInPalletes()) return
        if (this.isRoot()) return this.setInnerBacklight(side !== null)
        if (this.canvas.backlight_component !== null) {
            this.canvas.backlight_component.body.style.boxShadow = ''
        }
        this.canvas.backlight_component = this
        this.body.style.boxShadow = side === null ? '' : OuterBacklight[side]
    }
    
    setInnerBacklight (enabled=true) {
        if (this.isInPalletes()) return
        if (this.canvas.backlight_component !== null) {
            this.canvas.backlight_component.body.style.boxShadow = ''
        }
        this.canvas.backlight_component = this
        this.body.style.boxShadow = enabled ? InnerBacklight : ''
    }

    toGeety () {
        let properties = {}
        this.properties.forEach(property => {
            properties[property.key] = property.onload(this.body.querySelector('*'))  
        })
        let props = Object.keys(properties).length ? ` F:Properties="${escapeXML(JSON.stringify(properties))}"` : ''
        let xml = `<${this.gtag}${props}>`
        for (let child of this.children) {
            xml += child.toGeety()
        }
        xml += `</${this.gtag}>`
        return xml
    }
}
