class AttributedDict(dict):
    def __init__(self, *args, **kwargs):
        if args[0] is None:
            self = None
        else:
            dict.__init__(self, *args, **kwargs)

    def __getattr__(self, item):
        return self[item]
