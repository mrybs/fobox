class Modal {
    constructor (data) {
        this.data = data
        this.background = document.createElement('div')
        this.background.classList.add('modal-background')

        this.element = document.createElement('div')
        this.element.classList.add('modal')

        this.header = document.createElement('div')
        this.header.classList.add('modal-header')

        this.content = document.createElement('div')
        this.content.classList.add('modal-content')

        this.buttons = document.createElement('div')
        this.buttons.classList.add('modal-buttons')

        if (this.data.hasOwnProperty('title')) {
            this.header.innerHTML += `
                <h2>${this.data.title}</h2>
            `
        }
        this.header.innerHTML += `
            <span class="material-symbols-outlined modal-close">close</span>
        `

        if (this.data.hasOwnProperty('content')) {
            this.content.innerHTML += this.data.content
        }

        if (this.data.hasOwnProperty('buttons')) {
            this.data.buttons.forEach(button => {
                let button_element = document.createElement('button')
                if (button.hasOwnProperty('accent') && button.accent) {
                    button_element.classList.add('accent')
                }
                if (button.hasOwnProperty('icon')) {
                    button_element.innerHTML = `
                        <span class="material-symbols-outlined">${button.icon}</span>
                    `
                }
                button_element.innerHTML += button.label
                button_element.onclick = async (event) => await button.action(event, this)
                this.buttons.appendChild(button_element)
            })
        }

        this.element.appendChild(this.header)
        this.element.appendChild(this.content)
        this.element.appendChild(this.buttons)
        this.background.appendChild(this.element)
        document.body.appendChild(this.background)

        this.header.querySelector('.modal-close').onclick = () => {
            this.close()
        }
    }

    show () {
        this.background.style.display = 'flex'
        setTimeout(() => {
            this.background.style.opacity = 1
        }, 1)
        
    }

    close () {
        this.background.style.opacity = 0
        setTimeout(() => {
            this.background.remove()
        }, 150)
    }
}

class Alert {
    constructor (text) {
        this.text = text
        this.background = document.createElement('div')
        this.background.classList.add('modal-background')
        this.background.classList.add('alert-background')
        this.background.onclick = () => this.close()

        this.element = document.createElement('div')
        this.element.classList.add('modal')
        this.element.classList.add('alert')
        this.element.onclick = event => event.stopImmediatePropagation() 

        this.header = document.createElement('div')
        this.header.classList.add('modal-header')

        this.content = document.createElement('div')
        this.content.classList.add('modal-content')

        this.buttons = document.createElement('div')
        this.buttons.classList.add('modal-buttons')

        this.header.innerHTML += `
            <span class="material-symbols-outlined modal-close">close</span>
        `

        this.content.innerHTML += this.text

        ;[
            {
                label: 'Закрыть',
                icon: 'close',
                action: () => this.close(),
                accent: true
            }
        ].forEach(button => {
            let button_element = document.createElement('button')
            if (button.hasOwnProperty('accent') && button.accent) {
                button_element.classList.add('accent')
            }
            if (button.hasOwnProperty('icon')) {
                button_element.innerHTML = `
                    <span class="material-symbols-outlined">${button.icon}</span>
                `
            }
            button_element.innerHTML += button.label
            button_element.onclick = async (event) => await button.action(event, this)
            this.buttons.appendChild(button_element)
        })

        this.element.appendChild(this.content)
        this.element.appendChild(this.buttons)
        this.background.appendChild(this.element)
        document.body.appendChild(this.background)

        this.header.querySelector('.modal-close').onclick = () => {
            this.close()
        }
    }

    show () {
        this.background.style.display = 'flex'
        setTimeout(() => {
            this.background.style.opacity = 1
        }, 1)
        
    }

    close () {
        this.background.style.opacity = 0
        setTimeout(() => {
            this.background.remove()
        }, 150)
    }
}
