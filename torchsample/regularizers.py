
import torch as th
from fnmatch import fnmatch


class RegularizerModule(object):

    def __init__(self, regularizers):
        self.regularizers = regularizers
        self.loss = 0.

    def _apply(self, module, regularizer):
        for name, module in module.named_children():
            if fnmatch(name, regularizer.module_filter) and hasattr(module, 'weight'):
                self.loss += regularizer(module)
            self._apply(module, regularizer)

    def __call__(self, model):
        self.loss = 0.
        for regularizer in self.regularizers:
            self._apply(model, regularizer)
        return self.loss

    def __len__(self):
        return len(self.regularizers)


class L1Regularizer(object):

    def __init__(self, scale=0, module_filter='*'):
        self.scale = float(scale)
        self.module_filter = module_filter

    def __call__(self, module):
        w = module.weight
        value = th.sum(th.abs(w))
        loss = self.scale * value
        return loss


class L2Regularizer(object):

    def __init__(self, scale=0, module_filter='*'):
        self.scale = float(scale)
        self.module_filter = module_filter

    def __call__(self, module):
        w = module.weight
        value = th.sum(th.pow(w,2)) * self.scale
        loss = self.scale * value
        return loss


class L1L2Regularizer(object):

    def __init__(self, l1_scale=0, l2_scale=0, module_filter='*'):
        self.l1 = L1Regularizer(l1_scale)
        self.l2 = L2Regularizer(l2_scale)
        self.module_filter = module_filter

    def __call__(self, module):
        return self.l1(module) + self.l2(module)

