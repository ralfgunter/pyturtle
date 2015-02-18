from turtle_apply import apply_BinOp
from turtle_cfg_visitor import cfg_visit
from turtle_expr_visitor import reassign_expr_visit_dispatch
import turtle_ast as AST

# ---------------------------------------------------------------------------- #
class ConstantFolding(object):
    def constant_folding_visitor(node, toggle):
        def expr_visitor(expr, stmt):
            if isinstance(expr, AST.BinOp) and isinstance(expr.el, AST.NumLiteral) and isinstance(expr.er, AST.NumLiteral):
                toggle(expr, stmt)
                return AST.NumLiteral(apply_BinOp(expr))
            else:
                return expr

        if type(node) is Assignment:
            node.rval = reassign_expr_visit_dispatch(node.rval, node, expr_visitor)
        elif type(node) is IfStmt:
            node.pred = reassign_expr_visit_dispatch(node.pred, node, expr_visitor)
        elif type(node) is Repeat:
            node.times = reassign_expr_visit_dispatch(node.times, node, expr_visitor)
        elif type(node) is ExprStmt:
            node.expr = reassign_expr_visit_dispatch(node.expr, node, expr_visitor)
        elif type(node) is ReturnStmt and node.expr is not None:
            node.expr = reassign_expr_visit_dispatch(node.expr, node, expr_visitor)

    def constant_folding(ast, cfg):
        # FIXME: if changed is a primitive boolean, updating it in 'toggle'
        #        with |= does not update the reference in this scope
        changed = [False]
        def toggle(expr, node):
            changed[0] = True

        cfg_visit(cfg, ast_visitor_pre = lambda node: constant_folding_visitor(node, toggle))

        return changed[0]

# ---------------------------------------------------------------------------- #
class ConstantPropagation(object):
    def constant_propagation_visitor(node, toggle, assignment_map):
        def expr_visitor(expr, stmt):
            if type(expr) is StrExpr and type(assignment_map[expr].rval) is NumLiteral:
                toggle(expr, stmt)
                return assignment_map[expr].rval
            else:
                return expr

        if type(node) is Assignment and type(node.rval) is not Phi:
            node.rval = reassign_expr_visit_dispatch(node.rval, node, expr_visitor)
        elif type(node) is IfStmt:
            node.pred = reassign_expr_visit_dispatch(node.pred, node, expr_visitor)
        elif type(node) is Repeat:
            node.times = reassign_expr_visit_dispatch(node.times, node, expr_visitor)
        elif type(node) is ExprStmt:
            node.expr = reassign_expr_visit_dispatch(node.expr, node, expr_visitor)
        elif type(node) is ReturnStmt and node.expr is not None:
            node.expr = reassign_expr_visit_dispatch(node.expr, node, expr_visitor)

    def constant_propagation(ast, cfg):
        assignment_map = {}
        def collect_assignments_visitor(node):
            if type(node) is Assignment:
                assignment_map[node.lval] = node

        # FIXME: if changed is a primitive boolean, updating it in 'toggle'
        #        with |= does not update the reference in this scope
        changed = [False]
        def toggle(expr, node):
            changed[0] = True

        cfg_visit(cfg, ast_visitor_pre = collect_assignments_visitor)
        cfg_visit(cfg, ast_visitor_pre = lambda node: constant_propagation_visitor(node, toggle, assignment_map))

        return changed[0]
