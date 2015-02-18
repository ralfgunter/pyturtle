import copy
import turtle_ast as AST

from turtle_ctx import Context
from turtle_state import TurtleState
from turtle_func import Function

from multipledispatch import dispatch

# ---------------------------------------------------------------------------- #
class TurtleInterpreter(object):
    class ReturnFromFunc(Exception): pass

    binop_table = {
        '+': lambda a,b: a + b,
        '-': lambda a,b: a - b,
        '*': lambda a,b: a * b,
        '/': lambda a,b: a / b,

        '<':  lambda a,b: a < b,
        '>':  lambda a,b: a > b,
        '<=': lambda a,b: a <= b,
        '>=': lambda a,b: a >= b,
        '==': lambda a,b: a == b,
        '!=': lambda a,b: a != b
    }

    def __init__(self):
        self.builtins_table = {
            'FORWARD':  self.builtin_Forward,
            'FD':       self.builtin_Forward,
            'BACKWARD': self.builtin_Backward,
            'BK':       self.builtin_Backward,

            'RIGHT': self.builtin_Right,
            'RT':    self.builtin_Right,
            'LEFT':  self.builtin_Left,
            'LT':    self.builtin_Left,

            'PENUP':   self.builtin_PenUp,
            'PENDOWN': self.builtin_PenDown,

            'PUSH': self.builtin_Push,
            'POP':  self.builtin_Pop,

            'PRINT': self.builtin_Print,

            'CLEARSCREEN': self.builtin_Clearscreen
        }

        self.curr_ctx = Context()

        self.state = TurtleState()
        self.state_stack = [self.state]

    @dispatch(AST.Repeat)
    def turtle_apply(self, node):
        i = 0
        while i < int(self.turtle_apply(node.times)):
            self.turtle_apply(node.body)
            i += 1
        return None

    @dispatch(AST.Assignment)
    def turtle_apply(self, node):
        ident = node.lval.name
        val   = self.turtle_apply(node.rval)
        self.curr_ctx.add_ident(ident, val)
        return None

    @dispatch(AST.ExprStmt)
    def turtle_apply(self, node):
        return self.turtle_apply(node.expr)

    @dispatch(AST.FunExpr)
    def turtle_apply(self, node):
        if node.name in self.builtins_table:
            self.builtins_table[node.name](node)
        else:
            func_ident = node.name
            func = self.curr_ctx.get_ident(func_ident)
            enclosing_ctx = func.enclosing_ctx

            local_ctx = Context(enclosing_ctx)
            for name, arg in zip(func.arg_names, node.args):
                local_ctx.add_ident(name, self.turtle_apply(arg))

            tmp = self.curr_ctx
            self.curr_ctx = local_ctx

            self.turtle_apply(func.body)

            self.curr_ctx = tmp

        return None

    @dispatch(AST.FunctionDecl)
    def turtle_apply(self, node):
        ident = node.name
        arg_names = [arg.name for arg in node.args]
        body = node.body
        func = Function(ident, arg_names, body, self.curr_ctx)
        self.curr_ctx.add_ident(ident, func)
        return None

    @dispatch(AST.IfStmt)
    def turtle_apply(self, node):
        flag = self.turtle_apply(node.pred)
        if flag:
            return self.turtle_apply(node._then)
        elif node._else is not None:
            return self.turtle_apply(node._else)
        else:
            return None

    @dispatch(AST.NumLiteral)
    def turtle_apply(self, node):
        return node.num

    @dispatch(AST.StrExpr)
    def turtle_apply(self, node):
        return self.curr_ctx.get_ident(node.name)

    @dispatch(AST.BinOp)
    def turtle_apply(self, node):
        binop_handle = self.binop_table[node.op]
        el = self.turtle_apply(node.el)
        er = self.turtle_apply(node.er)
        return binop_handle(el,er)

    @dispatch(AST.Top)
    def turtle_apply(self, node):
        self.turtle_apply(node.body)
        return None

    @dispatch(AST.End)
    def turtle_apply(self, node):
        print('final state: '),
        print(self.state)
        return None

    @dispatch(AST.Seq)
    def turtle_apply(self, node):
        # FIXME!?!
        try:
            for n in node.lst:
                self.turtle_apply(n)
            return None
        except TurtleInterpreter.ReturnFromFunc:
            # Propagate the STOP command upwards until we hit the original function scope
            if (node.parent is not None) and (not isinstance(node.parent, AST.FunctionDecl)):
                raise TurtleInterpreter.ReturnFromFunc
            return None

    @dispatch(AST.ReturnStmt)
    def turtle_apply(self, node):
        raise TurtleInterpreter.ReturnFromFunc

    # ---------------------------------------------------------------------------- #
    def builtin_Forward(self, node):
        distance = self.turtle_apply(node.args[0])
        self.state.forward(distance)

    def builtin_Backward(self, node):
        distance = self.turtle_apply(node.args[0])
        self.state.forward(-distance)

    def builtin_Right(self, node):
        angle = self.turtle_apply(node.args[0])
        self.state.rotate(angle)

    def builtin_Left(self, node):
        angle = self.turtle_apply(node.args[0])
        self.state.rotate(-angle)

    def builtin_PenUp(self, node):
        self.state.pen('up')

    def builtin_PenDown(self, node):
        self.state.pen('down')

    def builtin_Push(self, node):
        self.state_stack.append(copy.deepcopy(self.state))

    def builtin_Pop(self, node):
        self.state = self.state_stack[-1]
        self.state_stack.pop()

    def builtin_Clearscreen(self, node):
        self.state.clearscreen()

    def builtin_Print(self, node):
        value = self.turtle_apply(node.args[0])
        print(value)
