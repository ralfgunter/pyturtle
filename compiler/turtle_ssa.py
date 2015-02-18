import turtle_ast as AST
from turtle_dominator import *
from turtle_cfg import CFG
from turtle_forward_dfa import ReachingDefinitions
from turtle_expr_visitor import expr_visit_dispatch

import copy
from multipledispatch import dispatch

class SSA(object):
    def __init__(self):
        self.var_write_table = {}

    def visit(self, node):
        self.enumerate_assignments(node)

    @dispatch(AST.FunctionDecl)
    def enumerate_assignments(self, node):
        for var in node.args:
            var_name = var.name
            if var_name in self.var_write_table:
                self.var_write_table[var_name] += 1
                var.ssa_idx = self.var_write_table[var_name]
            else:
                self.var_write_table[var_name] = 0

    @dispatch(AST.Assignment)
    def enumerate_assignments(self, node):
        var = node.lval
        var_name = var.name
        if var_name in self.var_write_table:
            self.var_write_table[var_name] += 1
            var.ssa_idx = self.var_write_table[var_name]
        else:
            self.var_write_table[var_name] = 0

    @dispatch(AST.ASTNode)
    def enumerate_assignments(self, node):
        pass

    def insert_phis(self, cfg):
        def collect_conflicts(rds, var):
            return filter(lambda rdef: rdef.name == var.name, rds)

        def traverse_phi_chain(fnode, var):
            curr = fnode
            while (type(curr.ast_node) is AST.Assignment) and (type(curr.ast_node.rval) is AST.Phi):
                if curr.ast_node.lval.name == var.name:
                    return True
                elif len(curr.succ) == 1:
                    curr = curr.succ[0]

            return False

        def insert_phi(fnode, var):
            def substitute(lst, orig, new):
                return [new if elem == orig else elem for elem in lst]

            previous_defs = collect_conflicts(reaching_defs[fnode], var)

            phi = AST.Phi([copy.deepcopy(previous_defs[0]), copy.deepcopy(previous_defs[1])])

            self.var_write_table[var.name] += 1
            join_var = AST.StrExpr(var.name, self.var_write_table[var.name])

            new_node = AST.Assignment(join_var, phi)

            cfg_node = cfg.new_node(new_node)
            cfg_node.succ = [fnode]
            cfg_node.prev = fnode.prev
            for pred in cfg_node.prev:
                pred.succ = substitute(pred.succ, fnode, cfg_node)
            fnode.prev = [cfg_node]

        changed = True
        while changed:
            changed = False

            doms = Dominators(cfg)
            doms.start()
            idoms = get_idoms(cfg, doms.out_set)
            dom_frontier = get_df(cfg, idoms)
            rd = ReachingDefinitions(cfg)
            rd.start()
            reaching_defs = rd.out_set

            for node_idx, frontier in dom_frontier.items():
                node = cfg.lst[node_idx]
                # FIXME: Hmm...
                if changed:
                    break

                if frontier and (type(node.ast_node) is AST.Assignment):
                    var = node.ast_node.lval
                    for fnode_idx in frontier:
                        fnode = cfg.lst[fnode_idx]
                        already_joined = traverse_phi_chain(fnode, var)
                        if (not already_joined) and (len(collect_conflicts(reaching_defs[fnode], var)) == 2):
                            insert_phi(fnode, var)
                            changed = True
                            break

        rd = ReachingDefinitions(cfg)
        rd.start()

        def update_read_ssa_index(expr, stmt):
            if type(expr) is AST.StrExpr:
                for val in rd.in_set[stmt]:
                    if expr.name == val.name:
                        expr.ssa_idx = val.ssa_idx

        for node in cfg:
            anode = node.ast_node
            if (type(anode) is AST.Assignment) and (type(anode.rval) is not AST.Phi):
                expr_visit_dispatch(anode.rval, node, update_read_ssa_index)
            elif type(anode) is AST.ExprStmt:
                expr_visit_dispatch(anode.expr, node, update_read_ssa_index)
            elif type(anode) is AST.IfStmt:
                expr_visit_dispatch(anode.pred, node, update_read_ssa_index)
            elif type(anode) is AST.Repeat:
                expr_visit_dispatch(anode.times, node, update_read_ssa_index)
            elif type(anode) is AST.ReturnStmt:
                expr_visit_dispatch(anode.expr, node, update_read_ssa_index)
