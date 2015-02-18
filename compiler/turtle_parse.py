from abc import ABCMeta, abstractmethod
import string
import turtle_ast as AST

# ---------------------------------------------------------------------------- #
class ParsingFailure(Exception):
    pass

# ---------------------------------------------------------------------------- #
class Parser(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse(self, tokens):
        pass

# ---------------------------------------------------------------------------- #
class RecursiveDescent(Parser):
    def __init__(self):
        pass

    def parse(self, tokens):
        self.tokens = tokens
        _, node = self.program(0)
        return node

    def program(self, j):
        i, body_node = self.body(j)
        i, _ = self.at_end(i)

        top_node = AST.Top(body_node)
        top_node.set_pos(j, i, " ".join(self.tokens[j:i-1]))

        return i, top_node

    def body(self, j):
        i, lst = self.maybe_many(j, self.stmt)

        joint = AST.Seq(lst)
        joint.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, joint

    def stmt(self, i):
        return self.rule_or(i, [self.fun_decl, self.fun_stmt])

    def fun_stmt(self, i):
        return self.rule_or(i, [self.function, self.assignment, self.conditional, self.repeat, self.return_stmt])

    def function(self, j):
        i, name = self.fun_name(j)
        i, lst = self.maybe_many(i, self.expr)

        fun_expr = AST.FunExpr(name, lst)
        fun_expr.set_pos(j, i, " ".join(self.tokens[j:i]))

        fun_node = AST.ExprStmt(fun_expr)
        fun_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, fun_node

    def fun_param(self, i):
        return self.rule_or(i, [self.number, self.var_name])

    def repeat(self, j):
        i, _ = self.one_of(j, ['REPEAT'])
        i, times = self.expr(i)
        i, _ = self.one_of(i, ['['])
        i, body_node = self.body(i)
        i, _ = self.one_of(i, [']'])

        repeat_node = AST.Repeat(times, body_node)
        repeat_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, repeat_node

    def assignment(self, j):
        i, _ = self.one_of(j, ['MAKE'])
        i, lval  = self.var_name(i)
        i, rval = self.expr(i)

        make_node = AST.Assignment(lval, rval)
        make_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, make_node

    def expr1(self, j):
        i, op = self.one_of(j, ['-', '+'])
        i, term_node = self.term(i)

        binop_node = AST.BinOp(None, op, term_node)
        binop_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, binop_node

    def expr2(self, j):
        i, op = self.one_of(j, ['*', '/'])
        i, factor_node = self.factor(i)

        binop_node = AST.BinOp(None, op, factor_node)
        binop_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, binop_node

    def parens_expr(self, j):
        i, _ = self.one_of(j, ['('])
        i, expr_node  = self.expr(i)
        i, _ = self.one_of(i, [')'])

        expr_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, expr_node

    def expr(self, j):
        i, head_node = self.term(j)
        i, lst = self.maybe_many(i, self.expr1)

        if lst:
            lst[0].el = head_node
            head_node.parent = lst[0]

            prev = lst[0]
            for curr in lst[1:]:
                curr.el = prev
                prev.parent = curr
                prev = curr

            prev.set_pos(j, i, " ".join(self.tokens[j:i]))

            return i, prev
        else:
            return i, head_node

    def term(self, j):
        i, head_node = self.factor(j)
        i, lst = self.maybe_many(i, self.expr2)

        if lst:
            lst[0].el = head_node
            head_node.parent = lst[0]

            prev = lst[0]
            for curr in lst[1:]:
                curr.el = prev
                prev.parent = curr
                prev = curr

            prev.set_pos(j, i, " ".join(self.tokens[j:i]))

            return i, prev
        else:
            return i, head_node

    def factor(self, i):
        return self.rule_or(i, [self.parens_expr, self.ident])

    def fun_decl(self, j):
        i, _ = self.one_of(j, ['TO'])
        i, name = self.fun_name(i)
        i, args = self.maybe_many(i, self.var_name)
        i, body_node = self.body(i)
        i, _ = self.one_of(i, ['END'])

        func_node = AST.FunctionDecl(name, args, body_node)
        func_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, func_node

    def ifnoelse(self, j):
        i, _ = self.one_of(j, ['IF'])
        i, pred = self.condition(i)
        i, _ = self.one_of(i, ['['])
        i, _then = self.body(i)
        i, _ = self.one_of(i, [']'])

        if_node = AST.IfStmt(pred, _then)
        if_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, if_node

    def ifelse(self, j):
        i, _ = self.one_of(j, ['IFELSE'])
        i, pred = self.condition(i)
        i, _ = self.one_of(i, ['['])
        i, _then = self.body(i)
        i, _ = self.one_of(i, [']'])
        i, _ = self.one_of(i, ['['])
        i, _else = self.body(i)
        i, _ = self.one_of(i, [']'])

        if_node = AST.IfStmt(pred, _then, _else)
        if_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, if_node

    def conditional(self, i):
        return self.rule_or(i, [self.ifnoelse, self.ifelse])

    def condition(self, j):
        i, id_node_1 = self.expr(j)
        i, comp_op = self.comp(i)
        i, id_node_2 = self.expr(i)

        comp_node = AST.BinOp(id_node_1, comp_op, id_node_2)
        comp_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, comp_node

    def ident(self, i):
        return self.rule_or(i, [self.var_name, self.number])

    def var_name(self, j):
        i, _ = self.one_of(j, [':'])
        i, name = self.fun_name(i)

        var_node = AST.StrExpr(':' + name)
        var_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, var_node

    def comp(self, i):
        return self.one_of(i, ['<', '<=', '==', '!=', '>=', '>'])

    def bin_op(self, i):
        return self.one_of(i, ['+', '-', '*', '/'])

    def return_stmt(self, j):
        i, ret = self.one_of(j, ['STOP'])

        ret_node = AST.ReturnStmt(ret)
        ret_node.set_pos(j, i, " ".join(self.tokens[j:i]))

        return i, ret_node

    def at_end(self, i):
        # None is the stack bottom flag (e.g. '$')
        i, _ = self.one_of(i, [None])

        node = AST.End()
        node.set_pos(i-1, i, "$")

        return i, node

    # ---------------------------------------------------------------------------- #
    # Parser combinators
    def rule_or(self, i, rules):
        for rule in rules:
            try:
                return rule(i)
            except ParsingFailure:
                continue

        raise ParsingFailure

    def maybe_many(self, i, rule):
        lst = []
        try:
            while True:
                # rule will eventually throw an exception,
                # breaking out of the loop
                i, node = rule(i)
                lst.append(node)
        except ParsingFailure:
            return i, lst

    def one_of(self, i, term_list):
        if self.tokens[i] in term_list:
            return i+1, self.tokens[i]
        else:
            raise ParsingFailure

    # ---------------------------------------------------------------------------- #
    def fun_name(self, i):
        reserved_keywords = ['TO', 'END', 'IF', 'IFELSE', 'REPEAT', 'MAKE', 'STOP',
                             '<', '<=', '>', '>=', '==', '!=',
                             '+', '-', '*', '/',
                             '[', ']']
        name = self.tokens[i]
        if name is None or name in reserved_keywords:
            raise ParsingFailure

        alphanum = list(string.ascii_letters) + [str(n) for n in range(10)]

        if name[0] not in list(string.ascii_letters):
            raise ParsingFailure

        if not all(c in alphanum for c in name[1:]):
            raise ParsingFailure

        return i+1, self.tokens[i]

    def number(self, i):
        try:
            num = float(self.tokens[i])

            node = AST.NumLiteral(num)
            node.set_pos(i, i+1, " ".join(self.tokens[i:i+1]))

            return i+1, node
        except (ValueError, TypeError):
            raise ParsingFailure

# ---------------------------------------------------------------------------- #
# Poor man's lexer
def fake_lex(string):
    toks = [':', '[', ']', '(', ')', '+', '-', '*', '/']
    for tok in toks:
        string = string.replace(tok, ' ' + tok + ' ')
    return string.split() + [None]
