#!/usr/bin/env python3
"""
SAT encoding for  (STS) in DIMACS CNF.

Idea:
- We precompute a valid round-robin schedule with the "circle method".
  That fixes WHO plays WHO each week (pairings).
  This already satisfies:
    (1) each pair plays exactly once
    (2) each team plays exactly once per week

- SAT then decides only WHERE to place each weekly match:
    X_w_m_p = match m of week w is put in period p

SAT constraints enforce:
  A) each match goes to exactly one period
  B) each period has exactly one match per week
  C) each team appears in the same period at most twice over all weeks

"""

from itertools import combinations

# Global CNF state

clauses = []
var_index = {}
reverse_var = []
next_var = 1

# We also keep the precomputed pairings for decoding.
# weeks[w] = list of matches (a,b), teams are 1..n
weeks = []


def new_var(name: str) -> int:
    global next_var
    if name in var_index:
        return var_index[name]
    var_index[name] = next_var
    reverse_var.append(name)
    next_var += 1
    return var_index[name]


def add_clause(lits):
    """
    Add a CNF clause (list of ints) without trailing 0.
    """
    clauses.append(lits)


def exactly_one(lits):
    """
    CNF for exactly one:
      - at least one: (l1 OR l2 OR ... OR lk)
      - at most one: pairwise (-li OR -lj)
    This is fine because our sets are size <= n/2 (<=12 for n=24).
    """
    if not lits:
        return
    add_clause(lits[:])  # at least one
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            add_clause([-lits[i], -lits[j]])

def at_most_2_seq(lits, tag):
    """
    CNF encoding of sum(lits) <= 2 using two sequential chains.
    We build two sequences:
      s[i] = among x0..xi, at least 1 is true
      t[i] = among x0..xi, at least 2 are true

    Then we dontallow a 3rd true:
      xi & t[i-1] -> False
    """
    n = len(lits)
    if n <= 2:
        return

    # s and t for i = 0..n-2 (we dont need them for the last position)
    s = [None] * (n - 1)
    t = [None] * (n - 1)

    for i in range(n - 1):
        s[i] = new_var(f"s_{tag}_{i}")
        t[i] = new_var(f"t_{tag}_{i}")

    add_clause([-lits[0], s[0]])
    # t0 stays unconstrained (it should be false naturally, but we don't need to force it)

    # Induction for i = 1..n-2, processing xi
    for i in range(1, n - 1):
        xi = lits[i]

        # xi -> s[i]
        add_clause([-xi, s[i]])
        # s[i-1] -> s[i]
        add_clause([-s[i - 1], s[i]])

        # (xi AND s[i-1]) -> t[i]
        add_clause([-xi, -s[i - 1], t[i]])
        # t[i-1] -> t[i]
        add_clause([-t[i - 1], t[i]])

        # t[i] -> s[i] (if we already have 2 trues then we definitely have 1 true)
        add_clause([-t[i], s[i]])

    # Forbid getting a 3rd true:
    # for i = 2..n-1:  xi AND t[i-1] -> False
    for i in range(2, n):
        xi = lits[i]
        add_clause([-xi, -t[i - 1]])


def at_most_2(lits):
    """
    CNF for at most 2:
    forbid any triple being all true:
      for all a<b<c:  (-a OR -b OR -c)
    Our list size is number of weeks (<=23 for n=24)
    """
    if len(lits) <= 2:
        return
    for a, b, c in combinations(lits, 3):
        add_clause([-a, -b, -c])


# Round-robin pairings(circle method)
def circle_method_pairings(n: int):

    if n % 2 != 0:
        raise ValueError("n must be even")

    teams = list(range(1, n + 1))
    fixed = teams[-1]
    rot = teams[:-1]

    W = n - 1
    half = n // 2
    out = []

    for _w in range(W):
        left = rot[:half - 1] + [fixed]
        right = rot[half - 1:][::-1]
        out.append(list(zip(left, right)))

        # rotate
        rot = [rot[-1]] + rot[:-1]

    return out

# DIMACS builder

def build_dimacs(n: int, use_sym: bool = False, anchor_week: int = 0):
    """
    Build the DIMACS CNF using X_w_m_p variables.
    """
    global clauses, var_index, reverse_var, next_var, weeks
    clauses = []
    var_index = {}
    reverse_var = []
    next_var = 1

    if n % 2 != 0:
        raise ValueError("n must be even")

    weeks = circle_method_pairings(n)

    W = n - 1
    P = n // 2
    M = n // 2  # matches per week

    def X(w, m, p):
        return new_var(f"X_{w}_{m}_{p}")
    
    for w in range(W):
        for m in range(M):
            for p in range(P):
                X(w, m, p)

    # 1. Each match (w,m) goes to exactly one period p
    for w in range(W):
        for m in range(M):
            exactly_one([X(w, m, p) for p in range(P)])

    # 2 Each period (w,p) contains exactly one match m
    for w in range(W):
        for p in range(P):
            exactly_one([X(w, m, p) for m in range(M)])

    # 3) Each team appears in the same period at most twice overall
    # For each team t and period p, collect the unique match index m(t,w) in each week w
    for t in range(1, n + 1):
        for p in range(P):
            lits = []
            for w in range(W):
                # find match index in week w that includes team t
                mtw = None
                for m, (a, b) in enumerate(weeks[w]):
                    if a == t or b == t:
                        mtw = m
                        break
            
                if mtw is None:
                    raise RuntimeError("circle method failed unexpectedly")

                lits.append(X(w, mtw, p))

            # Implied constraint    
            add_clause(lits[:])
            at_most_2(lits)
            #at_most_2_seq(lits, tag=f"T{t}_P{p}")

    # Symmetry breaking:
    # We can fix the period permutation by freezing week 0:
    #   match m of week 0 is placed in period m
    # This is safe because periods are interchangeable.
    if use_sym:
        aw = anchor_week % W
        # Freeze week 0
        for m in range(M):
            add_clause([X(aw, m, m)])

def get_reverse_map():
    return reverse_var[:]


def get_pairings():

    return weeks

def write_dimacs(path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"p cnf {next_var - 1} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(str(x) for x in cl) + " 0\n")
