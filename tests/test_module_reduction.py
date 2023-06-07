import re

from amaranth import *
from amaranth.back import rtlil

from .utils import *

class TM(Elaboratable):

    def __init__(self, W, op):
        self.W = W
        self.op = op

        self.x = Signal(self.W)
        self.y = Signal(self.W)
    

    def elaborate(self, platform):
        m = Module()
        m.setPureIdentifier(type(self), self.W, self.op)
        m.d.comb += self.y.eq(self.op(self.x))
        return m


class ReduceDuplicateModulesTestCase(FHDLTestCase):

    def test_2_not_3(self):
        m = Module()
        op = lambda x: x ^ (x + 1)
        m.submodules.a = a = TM(8, op)
        m.submodules.b = b = TM(8, op)
        m.d.comb += b.x.eq(a.y)
        S = rtlil.convert(m, ports=[a.x, b.y])
        n = len(re.findall(r"\bmodule\b", S))
        self.assertEqual(n, 2, f"{n} modules generated instead of only 2\n{S}")


    def test_3_not_5(self):
        m = Module()
        op = lambda x: x ^ (x + 1) #The problem with using a lambda for this is that if we where to recreate it, it wouldent give the same hash,
                                    # but it shows that a lot of different types of inputs work. Numbers, classes, functions, etc
        m.submodules.a = a = TM(8, op)
        m.submodules.b = b = TM(12, op)
        m.submodules.c = c = TM(8, op)
        m.submodules.d = d = TM(12, op)

        din = Signal(12)

        m.d.comb += [
            a.x.eq(din[:8]),
            b.x.eq(Cat(a.y, din[8:])),
            c.x.eq(b.y[:8]),
            d.x.eq(Cat(c.y, b.y[8:]))
        ]
        S = rtlil.convert(m, ports=[din, d.y])
        n = len(re.findall(r"\bmodule\b", S))
        self.assertEqual(n, 3, f"{n} modules generated instead of only 3\n{S}")
        