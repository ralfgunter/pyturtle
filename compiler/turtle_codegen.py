from turtle_ast import *
from turtle_cfg_visitor import cfg_visit

# ---------------------------------------------------------------------------- #
# FIXME FIXME FIXME
last_used_reg = 0
def get_temp_reg():
    global last_used_reg
    last_used_reg += 1
    return "$t%d" % last_used_reg

# Shared by IfStmt and the predicates (op_le, op_ge, op_eq, op_ne)
if_count = 0

# ---------------------------------------------------------------------------- #
def op_add(lreg, rreg):
    tmp_reg = get_temp_reg()
    code = "add %s,%s,%s\n" % (tmp_reg, lreg, rreg)
    return tmp_reg, code

def op_sub(lreg, rreg):
    tmp_reg = get_temp_reg()
    code = "sub %s,%s,%s\n" % (tmp_reg, lreg, rreg)
    return tmp_reg, code

def op_mult(lreg, rreg):
    tmp_reg = get_temp_reg()
    code  = "addi %s,%s,0\n" % (tmp_reg, lreg)
    code += "mult %s,%s\n"   % (tmp_reg, rreg)
    return tmp_reg, code

def op_div(lreg, rreg):
    tmp_reg = get_temp_reg()
    code  = "addi %s,%s,0\n" % (tmp_reg, lreg)
    code += "div  %s,%s\n"   % (tmp_reg, rreg)
    return tmp_reg, code


def op_lt(lreg, rreg):
    tmp_reg = get_temp_reg()
    code = "slt %s,%s,%s\n" % (tmp_reg, lreg, rreg)
    return tmp_reg, code

def op_gt(lreg, rreg):
    tmp_reg = get_temp_reg()
    code = "slt %s,%s,%s\n" % (tmp_reg, rreg, lreg)
    return tmp_reg, code

# TODO?: splitting integer & FP instructions would make this shorter
def op_le(lreg, rreg):
    tmp_reg = get_temp_reg()
    code  = "slt  %s,%s,%s\n" % (tmp_reg, rreg, lreg)
    code += "not  %s,%s\n"    % (tmp_reg, tmp_reg)
    code += "andi %s,%s,1\n"  % (tmp_reg, tmp_reg)
    return tmp_reg, code

def op_ge(lreg, rreg):
    tmp_reg = get_temp_reg()
    code  = "slt %s,%s,%s\n"  % (tmp_reg, lreg, rreg)
    code += "not %s,%s\n"     % (tmp_reg, tmp_reg)
    code += "andi %s,%s,1\n"  % (tmp_reg, tmp_reg)
    return tmp_reg, code

def op_eq(lreg, rreg):
    tmp_reg1 = get_temp_reg()
    tmp_reg2 = get_temp_reg()
    code  = "slt %s,%s,%s\n"    % (tmp_reg1, lreg, rreg)            # t1 = l < r
    code += "slt %s,%s,%s\n"    % (tmp_reg2, rreg, lreg)            # t2 = r < l
    code += "or  %s,%s,%s\n"    % (tmp_reg1, tmp_reg1, tmp_reg2)    # t3 = t1 | t2 <=> l != r
    code += "slt %s,$zero,%s\n" % (tmp_reg1, tmp_reg1)  # t3 > 0 <=> l == r
    return tmp_reg1, code

def op_ne(lreg, rreg):
    tmp_reg1 = get_temp_reg()
    tmp_reg2 = get_temp_reg()
    code  = "slt %s,%s,%s\n"  % (tmp_reg1, lreg, rreg)
    code += "slt %s,%s,%s\n"  % (tmp_reg2, rreg, lreg)
    code += "or  %s,%s,%s\n"  % (tmp_reg1, tmp_reg1, tmp_reg2)
    return tmp_reg, code

# ---------------------------------------------------------------------------- #
def builtin_Forward(expr):
    reg, instr = gen_expr_dispatch(expr.args[0])
    code  = instr
    code += "fd %s\n", reg
    return "", code

def builtin_Backward(expr):
    reg, instr = gen_expr_dispatch(expr.args[0])
    inv_reg, inv_instr = op_sub("$zero", reg)
    code  = instr + inv_instr
    code += "fd %s\n", inv_reg
    return "", code

def builtin_Right(expr):
    reg, instr = gen_expr_dispatch(expr.args[0])
    code  = instr
    code += "rt %s\n", reg
    return "", code

def builtin_Left(expr):
    reg, instr = gen_expr_dispatch(expr.args[0])
    inv_reg, inv_instr = op_sub("$zero", reg)
    code  = instr + inv_instr
    code += "rt %s\n", inv_reg
    return "", code

def builtin_PenUp(expr):
    return "", "pu\n"

def builtin_PenDown(expr):
    return "", "pd\n"

def builtin_Clearscreen(expr):
    return "", "cs\n"

# ---------------------------------------------------------------------------- #
def gen_expr_dispatch(expr):
    return expr_table[type(expr)](expr)

def gen_expr_Phi(expr):
    return "", ""

def gen_expr_NumLiteral(expr):
    value = expr.num
    tmp_reg = get_temp_reg()
    code = "li.s %s,%f\n" % (tmp_reg, value)
    return tmp_reg, code

def gen_expr_StrExpr(expr):
    return var_reg_table[expr.name], ""

def gen_expr_BinOp(expr):
    lreg, linstr = gen_expr_dispatch(expr.el)
    rreg, rinstr = gen_expr_dispatch(expr.er)
    oreg, oinstr = binop_table[expr.op](lreg, rreg)
    code  = linstr + rinstr + oinstr
    return oreg, code

def gen_expr_FunExpr(expr):
    if expr.name in builtin_table.keys():
        return builtin_table[expr.name](expr)
    else:
        raise NotImplemented

# ---------------------------------------------------------------------------- #
def gen_stmt_dispatch(stmt):
    return stmt_table[type(stmt)](stmt)

def gen_stmt_Assignment(stmt):
    ident = stmt.lval.name
    rreg, rinstr = gen_expr_dispatch(stmt.rval)

    if not var_reg_table.has_key(ident):
        lreg = get_temp_reg()
        var_reg_table[ident] = lreg

    lreg = var_reg_table[ident]
    code  = rinstr
    code += "addi %s,%s,0\n" % (lreg, rreg)
    return lreg, code

def gen_stmt_ExprStmt(stmt):
    return gen_expr_dispatch(stmt.expr)

def gen_stmt_IfStmt(stmt):
    global if_count

    pred_reg, pred_instr = gen_expr_dispatch(stmt.pred)
    code = pred_instr + ("beql %s,$zero,__if_%d_else\n" % (pred_reg, if_count))

    _, then_instr = gen_stmt_dispatch(stmt._then)
    code += then_instr + ("__if_%d_else:\n" % if_count)

    if stmt._else is not None:
        _, else_instr = gen_stmt_dispatch(stmt._else)
        code += else_instr

    code += "__if_%d_done:\n" % if_count

    if_count += 1

    return gen_expr_dispatch(stmt.expr)

# ---------------------------------------------------------------------------- #
final_code = ""
def visit_and_codegen(stmt):
    global final_code
    r = stmt_table[type(stmt)](stmt)
    final_code += r[1]

def linebreak(cfg_node):
    global final_code
    final_code += "\n"

def gen(cfg):
    cfg_visit(cfg, cfg_pre = linebreak, ast_post = visit_and_codegen)
    return final_code

# ---------------------------------------------------------------------------- #
stmt_table = {}

# stmt_table[Top] = gen_stmt_Top
stmt_table[IfStmt] = gen_stmt_IfStmt
stmt_table[ExprStmt] = gen_stmt_ExprStmt
# stmt_table[FunctionDecl] = gen_stmt_FunctionDecl
stmt_table[Assignment] = gen_stmt_Assignment
# stmt_table[Repeat] = gen_stmt_Repeat
# stmt_table[ReturnStmt] = gen_stmt_ReturnStmt
# stmt_table[type(None)] = lambda n,p,P: dummy_fun(n)

# ---------------------------------------------------------------------------- #
expr_table = {}

expr_table[Phi] = gen_expr_Phi
expr_table[NumLiteral] = gen_expr_NumLiteral
expr_table[StrExpr] = gen_expr_StrExpr
expr_table[BinOp] = gen_expr_BinOp
expr_table[FunExpr] = gen_expr_FunExpr
# expr_table[type(None)] = dummy_fun

# ---------------------------------------------------------------------------- #
binop_table = {}

binop_table['+'] = op_add
binop_table['-'] = op_sub
binop_table['*'] = op_mult
binop_table['/'] = op_div

binop_table['<'] = op_lt
binop_table['>'] = op_gt

# ---------------------------------------------------------------------------- #
builtin_table = {}

builtin_table['FORWARD']  = builtin_Forward
builtin_table['FD']       = builtin_Forward
builtin_table['BACKWARD'] = builtin_Backward
builtin_table['BK']       = builtin_Backward

builtin_table['RIGHT'] = builtin_Right
builtin_table['RT']    = builtin_Right
builtin_table['LEFT']  = builtin_Left
builtin_table['LT']    = builtin_Left

builtin_table['PENUP']   = builtin_PenUp
builtin_table['PENDOWN'] = builtin_PenDown

# builtin_table['PUSH'] = builtin_Push
# builtin_table['POP']  = builtin_Pop

# builtin_table['PRINT'] = builtin_Print

builtin_table['CLEARSCREEN']  = builtin_Clearscreen

# ---------------------------------------------------------------------------- #
var_reg_table = {}
