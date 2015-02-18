from abc import ABCMeta, abstractmethod

import turtle_ast as AST
import copy
import functools

class ForwardDataflowAnalysis(object):
    __metaclass__ = ABCMeta

    def __init__(self, cfg):
        self.cfg = cfg
        self.in_set = {}
        self.out_set = {}

    @abstractmethod
    def universal(self, node):
        pass

    @abstractmethod
    def gen(self, node):
        pass

    @abstractmethod
    def kill(self, node):
        pass

    @abstractmethod
    def conf(self, a, b):
        pass

    def start(self):
        self.initialize()
        self.analyze()

    def initialize(self):
        for node in self.cfg:
            self.in_set[node]  = self.universal(node)
            self.out_set[node] = self.universal(node)

    def _new_temp(self, node):
        return set.union(self.gen(node), set.difference(self.in_set[node], self.kill(node)))

    def analyze(self):
        changed = True

        while changed:
            changed = False

            for node in self.cfg:
                prevs = [self.out_set[n] for n in node.prev]
                if prevs:
                    self.in_set[node] = functools.reduce(self.conf, prevs)
                else:
                    self.in_set[node] = set()

                temp = self._new_temp(node)

                if temp != self.out_set[node]:
                    self.out_set[node] = copy.deepcopy(temp)
                    changed = True

class ReachingDefinitions(ForwardDataflowAnalysis):
    def universal(self, node):
        return set()

    def conf(self, a, b):
        return set.union(a,b)

    def gen(self, node):
        ast_node = node.ast_node

        s = set()
        if type(ast_node) is AST.Assignment:
            s.add(ast_node.lval)
        elif type(ast_node) is AST.FunctionDecl:
            s = set(ast_node.args)

        return s

    # Won't be used as we're redefining _new_temp below.
    def kill(self, node):
        return set()

    def _new_temp(self, node):
        return set.union(self.gen(node), self._kill(self.in_set[node], node))

    def _kill(self, in_set, node):
        ast_node = node.ast_node

        if type(ast_node) is AST.Assignment:
            var = ast_node.lval
            s = set(filter(lambda prev_var: prev_var.name != var.name, in_set))
        elif type(ast_node) is AST.FunctionDecl:
            var_names = (var.name for var in ast_node.args)
            s = set(filter(lambda prev_var: prev_var.name not in var_names, in_set))
        else:
            s = in_set

        return s
