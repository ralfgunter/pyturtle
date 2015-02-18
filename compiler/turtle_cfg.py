import pydot
import turtle_ast as AST

from multipledispatch import dispatch

# ---------------------------------------------------------------------------- #
class CFG(object):
    def __init__(self):
        self.lst = []

    def new_node(self, ast_node = None):
        n = CFGNode(idx = len(self.lst), ast_node = ast_node)
        self.lst.append(n)
        return n

    def visit_components(self, visitor):
        for node in self.lst:
            node.visited = False

        for node in self.lst:
            node.accept(visitor.pre_visit, visitor.post_visit)

    def __iter__(self):
        for n in self.lst:
            yield n

# ---------------------------------------------------------------------------- #
class CFGNode(object):
    def __init__(self, idx = -1, ast_node = None):
        self.prev = []
        self.succ = []
        self.ast_node = ast_node
        self.visited = False
        self.idx = idx

    def accept(self, cfg_pre_visitor, cfg_post_visitor):
        if not self.visited:
            self.visited = True

            cfg_pre_visitor(self)
            for succ in self.succ:
                succ.accept(cfg_pre_visitor, cfg_post_visitor)
            cfg_post_visitor(self)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.ast_node is not None:
            return str(self.ast_node)
        else:
            return "dummy"

# ---------------------------------------------------------------------------- #
@dispatch(AST.ExprStmt, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    nexpr = cfg.new_node(node)
    nprev.succ.append(nexpr)
    nexpr.prev.append(nprev)
    return nexpr

@dispatch(AST.Repeat, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    nstart = cfg.new_node(node)
    nstart.prev.append(nprev)
    nprev.succ.append(nstart)

    nbody = cfgfy(node.body, nstart, cfg)
    nbody.succ.append(nstart)
    nstart.prev.append(nbody)

    nexit = cfg.new_node()
    nexit.prev.append(nstart)
    nstart.succ.append(nexit)

    return nexit

@dispatch(AST.Assignment, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    n = cfg.new_node(node)
    n.prev.append(nprev)
    nprev.succ.append(n)
    return n

@dispatch(AST.FunctionDecl, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    nhandle = cfg.new_node(node)
    nhandle.prev.append(nprev)
    nprev.succ.append(nhandle)

    ndef = cfg.new_node(node)
    cfgfy(node.body, ndef, cfg)

    return nhandle

@dispatch(AST.IfStmt, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    ncond = cfg.new_node(node)
    nprev.succ.append(ncond)
    ncond.prev.append(nprev)

    join_node = cfg.new_node()

    st1 = node._then
    n1 = cfgfy(st1, ncond, cfg)
    n1.succ.append(join_node)
    join_node.prev.append(n1)

    st2 = node._else
    if st2 is not None:
        n2 = cfgfy(st2, ncond, cfg)
        n2.succ.append(join_node)
        join_node.prev.append(n2)
    else:
        ncond.succ.append(join_node)
        join_node.prev.append(ncond)

    return join_node

@dispatch(AST.ReturnStmt, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    nret = cfg.new_node(node)
    nprev.succ.append(nret)
    nret.prev.append(nprev)
    return nret

@dispatch(AST.Top, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    return cfgfy(node.body, nprev, cfg)

@dispatch(AST.Seq, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    ncurr = nprev

    for stmt in node.lst:
        n = cfgfy(stmt, ncurr, cfg)
        if n is not None:
            ncurr = n

    return ncurr

@dispatch(AST.End, CFGNode, CFG)
def cfgfy(node, nprev, cfg):
    nend = cfg.new_node(node)
    nprev.succ.append(nend)
    nend.prev.append(nprev)
    return nend

def ast_to_cfg(ast):
    cfg = CFG()
    ntop = cfg.new_node()
    cfgfy(ast, ntop, cfg)
    return cfg

# ---------------------------------------------------------------------------- #
## Draw graph.
class CFGGraphVisitor(object):
    def __init__(self):
        self.graph = pydot.Dot(graph_type = 'digraph')

    def pre_visit(self, node):
        label = str(node)
        if node.ast_node is not None:
            shape = "box"
        else:
            shape = "oval"
        # label = node.idx

        self.graph.add_node(pydot.Node(node.idx, label = str(node), shape = shape))

    def post_visit(self, node):
        for succ in node.succ:
            self.graph.add_edge(pydot.Edge(node.idx, succ.idx))

    def draw(self, filename):
        self.graph.write_png(filename)
