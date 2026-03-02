class Property:
    def __init__(
            self, 
            _type,
            key,
            name,
            onload, 
            onchange, 
            args):
        self.type = _type
        self.key = key
        self.name = name
        self.onload = onload
        self.onchange = onchange
        self.args = args
    
    def copy(self):
        return Property(
            self.type,
            self.key,
            self.name,
            self.onload,
            self.onchange,
            self.args
        )