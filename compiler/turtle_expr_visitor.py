from turtle_ast import *

# ---------------------------------------------------------------------------- #
def expr_visit_Phi(expr, stmt, fun):
    for val in expr.vals:
        expr_visit_dispatch(val, stmt, fun)
    fun(expr, stmt)

def expr_visit_NumLiteral(expr, stmt, fun):
    fun(expr, stmt)

def expr_visit_StrExpr(expr, stmt, fun):
    fun(expr, stmt)

def expr_visit_BinOp(expr, stmt, fun):
    expr_visit_dispatch(expr.el, stmt, fun)
    expr_visit_dispatch(expr.er, stmt, fun)
    fun(expr, stmt)

def expr_visit_FunExpr(expr, stmt, fun):
    for val in expr.args:
        expr_visit_dispatch(val, stmt, fun)
    fun(expr, stmt)

def expr_visit_dispatch(expr, stmt, fun):
    return expr_visit_table[type(expr)](expr, stmt, fun)

def dummy_fun(expr, stmt, fun):
    pass

# ---------------------------------------------------------------------------- #
expr_visit_table = {}
expr_visit_table[Phi] = expr_visit_Phi
expr_visit_table[NumLiteral] = expr_visit_NumLiteral
expr_visit_table[StrExpr] = expr_visit_StrExpr
expr_visit_table[BinOp] = expr_visit_BinOp
expr_visit_table[FunExpr] = expr_visit_FunExpr
expr_visit_table[type(None)] = dummy_fun


# ---------------------------------------------------------------------------- #
## Reassignment variant for constant folding, etc.
def reassign_expr_visit_Phi(expr, stmt, fun):
    for n, val in enumerate(expr.vals):
        expr.vals[n] = reassign_expr_visit_dispatch(val, stmt, fun)
    return fun(expr, stmt)

def reassign_expr_visit_NumLiteral(expr, stmt, fun):
    return fun(expr, stmt)

def reassign_expr_visit_StrExpr(expr, stmt, fun):
    return fun(expr, stmt)

def reassign_expr_visit_BinOp(expr, stmt, fun):
    expr.el = reassign_expr_visit_dispatch(expr.el, stmt, fun)
    expr.er = reassign_expr_visit_dispatch(expr.er, stmt, fun)
    return fun(expr, stmt)

def reassign_expr_visit_FunExpr(expr, stmt, fun):
    for n, val in enumerate(expr.args):
        expr.args[n] = reassign_expr_visit_dispatch(val, stmt, fun)
    return fun(expr, stmt)

def reassign_expr_visit_dispatch(expr, stmt, fun):
    return reassign_expr_visit_table[type(expr)](expr, stmt, fun)

def dummy_fun(expr, stmt, fun):
    return None

# ---------------------------------------------------------------------------- #
reassign_expr_visit_table = {}
reassign_expr_visit_table[Phi] = reassign_expr_visit_Phi
reassign_expr_visit_table[NumLiteral] = reassign_expr_visit_NumLiteral
reassign_expr_visit_table[StrExpr] = reassign_expr_visit_StrExpr
reassign_expr_visit_table[BinOp] = reassign_expr_visit_BinOp
reassign_expr_visit_table[FunExpr] = reassign_expr_visit_FunExpr
reassign_expr_visit_table[type(None)] = dummy_fun
