import geety
from bs4 import BeautifulSoup as bs


if __name__ == '__main__':
    page = geety.Page()
    page.load(open('geety/Components/Card.xml', 'r'))
    page.load(open('geety/index.xml', 'r'))
    page.set_entry_point('App')
    print(bs(page.html(), features='html.parser').prettify())
    #print(app.html())
    #print(app._components)
    #print(app._loaded['Card'].find_by_tag('arg'))
