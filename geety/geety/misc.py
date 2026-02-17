def print_tree(component, lvl=0) -> None:
    print(f'{"\t"*lvl}{component}')
    for child in component.children:
        print_tree(child, lvl+1)