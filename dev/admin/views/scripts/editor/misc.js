const XHTML_NS = "http://www.w3.org/1999/xhtml";
const ID_PREFIX = '_EditorElement-'
const ELEMENT_PATH_PREFIX = '_EditorElementPath-Id-'
const Sides = Object.freeze({
    LEFT: 'LEFT',
    TOP: 'TOP',
    RIGHT: 'RIGHT',
    BOTTOM: 'BOTTOM',
    INSIDE: 'INSIDE'
})
const OuterBacklight = Object.freeze({
    LEFT: '-10px 0 5px -5px var(--editor-backlight)',
    TOP: '0 -10px 5px -5px var(--editor-backlight)',
    RIGHT: '10px 0 5px -5px var(--editor-backlight)',
    BOTTOM: '0 10px 5px -5px var(--editor-backlight)'
})
const InnerBacklight = 'inset 0 0 5px 2px var(--editor-backlight)';
const PropertyTypes = Object.freeze({
    TEXT: 'TEXT',
    COLOR: 'COLOR',
    NUMBER: 'NUMBER',
    VARIANTS: 'VARIANTS'
})

function generateId () { return ID_PREFIX + Math.random().toString(36).substring(2, 15) }

function generateElementPathPrefix () { return ELEMENT_PATH_PREFIX + Math.random().toString(36).substring(2, 15)}

function getComponentId (element) {
    let parent = element
    while (!parent.id.startsWith(ID_PREFIX) && parent !== null) {
        parent = parent.parentNode
    }
    return parent !== null ? parent.id : null
}

function getContainer (canvas, element) {
    let container = canvas.getComponentById(getComponentId(element))
    while (!container.container) {
        container = canvas.getComponentById(getComponentId(element.parentNode))
    }
    return container !== null ? container : null
}

function getClosestWithSide (parent, x, y) {
    let closest = null
    let minDist = Infinity
    let side = null
    for (const el of parent.children) {
        const rect = el.getBoundingClientRect()
        const dx = Math.max(rect.left - x, 0, x - rect.right)
        const dy = Math.max(rect.top - y, 0, y - rect.bottom)
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < minDist) {
            minDist = dist
            closest = el
            if (dx === 0 && dy === 0) {
                side = Sides.INSIDE
            } else {
                let horizSide = null
                if (x < rect.left) horizSide = Sides.LEFT
                else if (x > rect.right) horizSide = Sides.RIGHT
                let vertSide = null
                if (y < rect.top) vertSide = Sides.TOP
                else if (y > rect.bottom) vertSide = Sides.BOTTOM
                if (horizSide && !vertSide) {
                    side = horizSide
                } else if (!horizSide && vertSide) {
                    side = vertSide
                } else if (horizSide && vertSide) {
                    if (dx > dy) {
                        side = horizSide
                    } else if (dy > dx) {
                        side = vertSide
                    } else {
                        side = horizSide
                    }
                } else {
                    side = null
                }
            }
        }
    }
    return {
        element: closest,
        side: side
    }
}

function getInnerXHTML (node) {
    var xdoc = document.implementation.createDocument(XHTML_NS, 'html', null);
    // Temporarily adopt/append the node into the new XML document
    xdoc.documentElement.appendChild(xdoc.importNode(node, true)); 
    // The innerHTML of the XML document's root element will be well-formed XHTML
    var xhtmlString = xdoc.documentElement.innerHTML;
    // Remove the appended node to clean up
    xdoc.documentElement.removeChild(xdoc.documentElement.lastChild);
    return xhtmlString;
}

function createNode (html) {
    let node = document.createElement('div')
    node.innerHTML = html
    return node.querySelector('*')
}

function escapeXML(xml) {
    return xml.replaceAll('"', '&quot;').replaceAll('\'', '&apos;')
}
