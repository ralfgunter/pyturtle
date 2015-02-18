class Function(object):
    def __init__(self, ident, arg_names, body, ctx):
        self.ident = ident
        self.arg_names = arg_names
        self.body = body
        self.enclosing_ctx = ctx
