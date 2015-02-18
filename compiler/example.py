import turtle_parse
import turtle_ast
import turtle_cfg
import turtle_ssa
# import turtle_optimize
import turtle_apply
# from turtle_codegen import gen

# string = """
# MAKE :X 2+3
# IF :X > 10
#     [
#         MAKE :X 5+6
#     ]
# MAKE :Y 10*:X
# """

# string = """
# MAKE :X 2+3
# IFELSE :X > 10
#     [
#         MAKE :X 5+6
#     ] [
#         MAKE :X 7+8
#     ]
# MAKE :Y 10*:X
# """

# string = """
# MAKE :X 2 + 3
# MAKE :Y 2 + (3 * (4 - (:X / 6)))
# MAKE :X :X + 2
# MAKE :Z :X + :Y
# """

# string = """
# TO FOO :X
#     TO BAR :Y
#         PRINT :X * :Y
#     END
#     BAR :X
# END
# FOO 10
# """

# string = """
# MAKE :A 10
# TO FOO :X
#     TO BAR :Y
#         PRINT :A + :Y
#     END
#     MAKE :A :A * 10
#     BAR :X
# END
# MAKE :A :A * 10
# FOO 10
# """

string = """
TO TREE :SIZE
   IF :SIZE < 5 [ FORWARD :SIZE BACKWARD :SIZE STOP ]
   FORWARD :SIZE / 3
   LEFT 30 TREE :SIZE * 2/3 RIGHT 30
   FORWARD :SIZE / 6
   RIGHT 25 TREE :SIZE / 2 LEFT 25
   FORWARD :SIZE / 3
   RIGHT 25 TREE :SIZE / 2 LEFT 25
   FORWARD :SIZE / 6
   BACKWARD :SIZE
END
CLEARSCREEN
TREE 150
"""

# string = """
# MAKE :X 123
# MAKE :Y :X + 2
# REPEAT :Y
# [
#     FD :Y
#     IFELSE :Y < 5 [
#         FD :X
#         MAKE :X :X+1
#     ] [
#         BK :X
#         MAKE :X :X-1
#     ]
#     MAKE :Y :Y+10
# ]
# MAKE :X 321
# FD :X
# FD :Y
# """

## Parse code above into an AST.
parser = turtle_parse.RecursiveDescent()
tokens = turtle_parse.fake_lex(string)
ast = parser.parse(tokens)

interpreter = turtle_apply.TurtleInterpreter()
interpreter.turtle_apply(ast)

## Print AST.
# ast_graph_visitor = turtle_ast.ASTGraphVisitor()
# ast.accept(ast_graph_visitor)
# ast_graph_visitor.draw('ast.png')
#
# ## Convert the AST to a CFG.
# cfg = turtle_cfg.ast_to_cfg(ast)
#
# ## Print CFG.
# cfg_graph_visitor = turtle_cfg.CFGGraphVisitor()
# cfg.visit_components(cfg_graph_visitor)
# cfg_graph_visitor.draw('pre_opt_cfg.png')
#
# ## Put CFG into SSA format.
# ssa = turtle_ssa.SSA()
# ast.accept(ssa)
# ssa.insert_phis(cfg)
#
# ## Do some optimizations on the CFG.
# changed = True
# while changed:
#     changed  = turtle_optimize.constant_folding(ast, cfg)
#     changed |= turtle_optimize.constant_propagation(ast, cfg)
#
# ## Print new CFG.
# cfg_graph_visitor = turtle_cfg.CFGGraphVisitor()
# cfg.visit_components(cfg_graph_visitor)
# cfg_graph_visitor.draw('post_opt_cfg.png')

## Generate assembly.
# print gen(cfg)
