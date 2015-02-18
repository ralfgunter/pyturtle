class Context(object):
    def __init__(self, parent = None):
        self.parent = parent
        self.table = {}

    def add_ident(self, ident, value):
        self.table[ident] = value

    def get_ident(self, ident):
        if ident in self.table.keys():
            return self.table[ident]
        elif self.parent is None:
            raise Exception("ident " + ident + " not found")
        else:
            return self.parent.get_ident(ident)
