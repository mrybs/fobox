class Geety{
    redirect = (href) => { window.location.href = href }
    $ = (query) => { return document.querySelector(query) }
    GET = async (url, params={}) => {
        const _url = new URL(url, document.baseURI)
        if (params) _url.search = new URLSearchParams(params).toString()
        return await fetch(_url)
    }
    GET_JSON = async (url, params={}) => { return await (await this.GET(url, params)).json() }
    POST = async (url, headers={}, body={}) => { return await fetch(url, { method: 'POST', 'headers': headers, 'body': body }) }
    rgbToHex = (rgb) => {
        if (rgb.startsWith('#')) {
            return rgb.toUpperCase()
        }
        const match = rgb.match(/\d+/g)
        if (!match) {
            return null
        }
        const r = parseInt(match[0], 10)
        const g = parseInt(match[1], 10)
        const b = parseInt(match[2], 10)
        const componentToHex = (c) => {
            const hex = c.toString(16)
            return hex.padStart(2, '0')
        }
        return `#${componentToHex(r)}${componentToHex(g)}${componentToHex(b)}`.toUpperCase()
    }
}

var G = new Geety()
