import geety


if __name__ == '__main__':
    app = geety.parse_component(open('geety/Components/Card.xml', 'r'))
    geety.print_tree(app)
