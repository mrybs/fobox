function showContextMenu (clientX, clientY, elements) {
    if (!document.hasOwnProperty('contextMenu')){
        document.contextMenu = document.createElement('div')
        document.contextMenu.id = 'editor-context-menu'
        document.querySelector('body').appendChild(document.contextMenu)
        window.onclick = event => {
            hideContextMenu()
        }
    }
    document.contextMenu.replaceChildren()
    elements.forEach(element => {
        let element_element = document.createElement('div')
        element_element.innerHTML = `
            <span class="material-symbols-outlined editor-context-menu-icon">${element.icon}</span>
            <span>${element.label}</span>
        `
        element_element.style.color = element.color
        element_element.onclick = event => {
            element.onclick(event)
            hideContextMenu()
        }
        document.contextMenu.appendChild(element_element)
    })
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight
    document.contextMenu.style.left = clientX + 'px'
    if (clientY + document.contextMenu.clientHeight >= viewportHeight) {
        document.contextMenu.style.bottom = '10px'
        document.contextMenu.style.top = 'inherit'
    } else {
        document.contextMenu.style.top = clientY + 'px'
        document.contextMenu.style.bottom = 'inherit'
    }
    document.contextMenu.style.display = 'block'
}

function hideContextMenu () {
    if (document.hasOwnProperty('contextMenu')){
        document.contextMenu.style.display = 'none'
    }
}
