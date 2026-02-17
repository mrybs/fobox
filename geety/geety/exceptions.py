class GeetyException(Exception): ...


class EntryPointNotSet(GeetyException): 
    def __init__(self):
        super().__init__('entry point has not set')


class ComponentAlreadyExists(GeetyException):
    def __init__(self, tag):
        super().__init__(f'component {tag} has redefined twice')


class DBException(GeetyException): ...

class DBContextMismatch(DBException):
    def __init__(self, cont_index, op_index, op_name):
        super().__init__(f'Database #{op_index} operation {op_name} cannot be used inside Database #{cont_index} context')


class DBCollectionNotSpecified(DBException):
    def __init__(self, cont_index):
        super().__init__(f'collection in Database #{cont_index} has not specified')