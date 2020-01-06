#!/usr/bin/python
from z3 import *
import sys

def solve(wanted_n, show_model=True):
  x_range = (129, 159)
  y_range = (298, 334)

  s = Solver()

  x = []
  y = []
  d = []
  for i in xrange(10):
    x.append(BitVec("x%i" % i, 32))
    y.append(BitVec("y%i" % i, 32))
    d.append(BitVec("d%i" % i, 32))
    s.add(x[i] >= x_range[0], x[i] <= x_range[1])
    s.add(y[i] >= y_range[0], y[i] <= y_range[1])
    s.add(d[i] >= 0, d[i] <= 3)

  n = BitVecVal(0xf0e1d2c3, 32)

  for i in xrange(10):
    k = x[i] ^ (y[i] << 8) ^ (d[i] << 16)
    n = ((n << 3) ^ k) & 0xffffffff
    #n = (n ^ (x[i] * 4960073981)) & 0xffffffff
    #n = (n + (y[i] * 5825700401)) & 0xffffffff
    #n = (n ^ (d[i] * 7922130913)) & 0xffffffff

  s.add(n == wanted_n)
  print s.check()

  if show_model:
    m = s.model()

    DIR_NORTH = 0
    DIR_SOUTH = 1
    DIR_WEST = 2
    DIR_EAST = 3

    dirs = "NSWE"
    for i in xrange(10):
      cx = m[x[i]].as_long()
      cy = m[y[i]].as_long()
      cd = m[d[i]].as_long()
      print "%i: (%i, %i, %i) %s" % (
        i, cx, cy, cd, dirs[cd]
      )

if len(sys.argv) != 2:
  sys.exit("usage: ./pickaxe_solver.py <number> (or TESTALL)")

if sys.argv[1] == "TESTALL":
  for i in xrange(100000):
    print "%i: " % i,
    sys.stdout.flush()
    solve(i, False)
    sys.stdout.flush()
else:
  wanted_n = int(sys.argv[1])
  print "Looking for: %i" % wanted_n
  solve(wanted_n)

