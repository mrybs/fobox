import geety


if __name__ == '__main__':
    app = geety.App()
    app.load('Card', open('geety/Components/Card.xml', 'r'))
    print(app.html())
    #print(app._loaded['Card'].find_by_tag('arg'))
