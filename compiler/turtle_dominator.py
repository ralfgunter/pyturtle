from turtle_forward_dfa import ForwardDataflowAnalysis

class Dominators(ForwardDataflowAnalysis):
    def universal(self, node):
        if node.prev:
            return set((n.idx for n in self.cfg))
        else:
            return set([node.idx])

    def conf(self, a, b):
        return set.intersection(a,b)

    def gen(self, node):
        return set([node.idx])

    def kill(self, node):
        return set()

def get_idoms(cfg, doms):
    idoms = {}

    for node in cfg:
        visited = set()
        q = [node]
        while len(q) > 0:
            curr = q.pop()

            if curr.idx not in visited:
                visited.add(curr.idx)

                if curr.idx in doms[node] and curr.idx != node.idx:
                    idoms[node] = curr
                    break
                else:
                    q = curr.prev + q

    return idoms

def get_df(cfg, idom):
    df = {}

    for node in cfg:
        df[node.idx] = set()

    for node in cfg:
        if len(node.prev) > 1:
            for pred in node.prev:
                runner = pred
                while runner != idom[node]:
                    df[runner.idx].add(node.idx)
                    runner = idom[runner]

    return df
