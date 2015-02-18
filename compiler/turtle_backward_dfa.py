from abc import ABCMeta, abstractmethod

import copy

class BackwardDataFlowAnalysis(object):
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

    def analyze(self):
        changed = True

        while changed:
            changed = False

            for node in self.cfg:
                succs = [self.in_set[n] for n in node.succ]
                if prevs:
                    self.out_set[node] = reduce(self.conf, succs)
                else:
                    self.out_set[node] = set()

                temp = set.union(self.gen(node), set.difference(self.out_set[node], self.kill(node)))

                if temp != self.in_set[node]:
                    self.in_set[node] = copy.deepcopy(temp)
                    changed = True
