from abc import ABCMeta, abstractmethod
import pydot

# ---------------------------------------------------------------------------- #
## Useful in error messages for user programs.
class PositionalMixin(object):
    def __init__(self, begin = -1, end = -1):
        self.begin_idx = begin
        self.end_idx   = end
        self.string = ""
        super(PositionalMixin, self).__init__()

    def set_pos(self, beg, end, string):
        self.begin_idx = beg
        self.end_idx = end
        self.string = string

# ---------------------------------------------------------------------------- #
class ASTNode(PositionalMixin):
    def __init__(self, parent = None):
        self.parent = parent
        super(ASTNode, self).__init__()

    def accept(self, visitor):
        raise NotImplemented("Default ASTNode accept function called on object " + str(self))

    def __str__(self):
        return "missing"

    def __repr__(self):
        return str(self)

# ---------------------------------------------------------------------------- #
class Statement(ASTNode):
    def __init__(self):
        super(Statement, self).__init__()

class FunctionDecl(Statement):
    def __init__(self, name, args, body):
        super(FunctionDecl, self).__init__()
        self.name = name
        self.args = args
        self.body = body
        self.body.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.body.accept(visitor)

    def __str__(self):
        args_string = " * ".join((str(arg) for arg in self.args))
        return "%s => %s" % (self.name, args_string)

class ExprStmt(Statement):
    def __init__(self, expr):
        super(ExprStmt, self).__init__()
        self.expr = expr
        self.expr.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.expr.accept(visitor)

    def __str__(self):
        return str(self.expr)

class Assignment(Statement):
    def __init__(self, lval, rval):
        super(Assignment, self).__init__()
        self.lval = lval
        self.rval = rval
        self.lval.parent = self
        self.rval.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.lval.accept(visitor)
        self.rval.accept(visitor)

    def __str__(self):
        return "%s = %s" % (str(self.lval), str(self.rval))

class Seq(Statement):
    def __init__(self, lst):
        super(Seq, self).__init__()
        self.lst = lst
        for c in self.lst:
            c.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        for node in self.lst:
            node.accept(visitor)

    def __str__(self):
        return "seq"

class IfStmt(Statement):
    def __init__(self, pred, _then, _else = None):
        super(IfStmt, self).__init__()
        self.pred = pred
        self._then = _then
        self._else = _else
        self.pred.parent = self
        self._then.parent = self
        if _else is not None:
            self._else.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.pred.accept(visitor)
        self._then.accept(visitor)
        if self._else is not None:
            self._else.accept(visitor)

    def __str__(self):
        return str(self.pred)

class Repeat(Statement):
    def __init__(self, times, body):
        super(Repeat, self).__init__()
        self.times = times
        self.body = body
        self.times.parent = self
        self.body.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.times.accept(visitor)
        self.body.accept(visitor)

    def __str__(self):
        return "REPEAT %s" % str(self.times)

class ReturnStmt(Statement):
    def __init__(self, kind, expr = None):
        super(ReturnStmt, self).__init__()
        self.kind = kind
        self.expr = expr
        if expr is not None:
            self.expr.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        if self.expr is not None:
            self.expr.accept(visitor)

    def __str__(self):
        return "RETURN %s" % ("" if self.expr is None else str(self.expr))

# ---------------------------------------------------------------------------- #
class Expression(ASTNode):
    pass

class Phi(Expression):
    def __init__(self, vals):
        super(Phi, self).__init__()
        self.vals = vals
        for val in vals:
            val.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        for val in self.rvals:
            val.accept(visitor)

    def __str__(self):
        vars_string = " ".join((str(var) for var in self.vals))
        return "PHI %s" % vars_string

class NumLiteral(Expression):
    def __init__(self, num):
        super(NumLiteral, self).__init__()
        self.num = num

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return str(self.num)

class BinOp(Expression):
    def __init__(self, el, op, er):
        super(BinOp, self).__init__()
        self.el = el
        self.op = op
        self.er = er
        if el is not None:
            self.el.parent = self
        if er is not None:
            self.er.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.el.accept(visitor)
        self.er.accept(visitor)

    def __str__(self):
        return "(%s %s %s)" % (str(self.el), str(self.op), str(self.er))

class StrExpr(Expression):
    def __init__(self, name, ssa_idx = 0):
        super(StrExpr, self).__init__()
        self.name = name
        self.ssa_idx = ssa_idx

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s(%d)" % (self.name, self.ssa_idx)

    # Needed for SSA
    def __hash__(self):
        return hash((self.name, self.ssa_idx))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.ssa_idx == other.ssa_idx
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

class FunExpr(Expression):
    def __init__(self, name, args):
        super(FunExpr, self).__init__()
        self.name = name
        self.args = args
        for arg in args:
            arg.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        for arg in self.args:
            arg.accept(visitor)

    def __str__(self):
        args_string = " ".join((str(arg) for arg in self.args))
        return "%s %s" % (self.name, args_string)

# ---------------------------------------------------------------------------- #
class Top(ASTNode):
    def __init__(self, body):
        super(Top, self).__init__()
        self.body = body
        self.body.parent = self

    def accept(self, visitor):
        visitor.visit(self)
        self.body.accept(visitor)

    def __str__(self):
        return "top"

class End(ASTNode):
    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "end"

# ---------------------------------------------------------------------------- #
## Draw graph.
class ASTGraphVisitor(object):
    def __init__(self):
        self.graph = pydot.Dot(graph_type = 'digraph')
        self.count = 0
        self.graph_idx = {}

    def visit(self, node):
        self.graph_idx[node] = self.count
        self.graph.add_node(pydot.Node(self.count, label = str(node)))
        if node.parent is not None:
            self.graph.add_edge(pydot.Edge(self.graph_idx[node.parent], self.count))
        self.count += 1

    def draw(self, filename):
        self.graph.write_png(filename)
