class Geety{
    redirect = (href) => { window.location.href = href; }
    $ = (query) => { return document.querySelector(query); }
    POST = async (url, _headers={}, _body={}) => { await fetch(url, { method: 'POST', headers: _headers, body: _body }) } 
}