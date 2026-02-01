#!/usr/bin/env python3
"""
SMT2 exporter for external solvers (cvc5 / OpenSMT).

Encoding uses Int vars per_{w,m} in [0..P-1] with (distinct ...) per week.
Fairness uses Bool home_{w,m}.
"""

from __future__ import annotations
from pathlib import Path
from round_robin import circle_method_pairs


def per_var(w, m) -> str:
    return f"per_{w}_{m}"


def home_var(w, m) -> str:
    return f"home_{w}_{m}"


def write_smt2_file(
    n: int,
    out_path: str | Path,
    *,
    use_sym: bool,
    with_home: bool,
    max_diff: int | None,
    add_implied_exact_counts: bool = True,
    add_team1_pins: int = 0,
    # symmetry break for home variables when optimizing
    fix_home_sym: bool = True,
):
    """
    Notes:
    - This is separate from the Z3 PB encoding. It's for external solvers only.
    - If max_diff is not None => with_home must be True.
    """
    if n % 2 != 0:
        raise ValueError("n must be even")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    P = n // 2
    W = n - 1
    weeks = circle_method_pairs(n)

    # Precompute match_of[w][t]
    match_of = [[None] * (n + 1) for _ in range(W)]
    for w in range(W):
        for m, (a, b) in enumerate(weeks[w]):
            match_of[w][a] = m
            match_of[w][b] = m
    for w in range(W):
        for t in range(1, n + 1):
            if match_of[w][t] is None:
                raise RuntimeError(f"Bad RR: team {t} missing in week {w}")

    with out_path.open("w", encoding="utf-8") as f:
        f.write("(set-logic QF_LIA)\n")
        f.write("(set-option :produce-models true)\n")

        # Decls
        for w in range(W):
            for m in range(P):
                f.write(f"(declare-fun {per_var(w,m)} () Int)\n")
                if with_home:
                    f.write(f"(declare-fun {home_var(w,m)} () Bool)\n")

        # Domains for per vars
        for w in range(W):
            for m in range(P):
                f.write(f"(assert (and (<= 0 {per_var(w,m)}) (< {per_var(w,m)} {P})))\n")

        # Distinct periods per week
        for w in range(W):
            vars_w = " ".join(per_var(w, m) for m in range(P))
            f.write(f"(assert (distinct {vars_w}))\n")

        # Team-period count constraints:
        # Base STS: count(t,p) <= 2
        # Implied structure: count(t,p) >= 1 and exactly one p with count(t,p)=1
        for t in range(1, n + 1):
            sum_exprs = []
            for p in range(P):
                terms = []
                for w in range(W):
                    m = match_of[w][t]
                    terms.append(f"(ite (= {per_var(w,m)} {p}) 1 0)")
                sum_expr = f"(+ {' '.join(terms)})"
                sum_exprs.append(sum_expr)

                f.write(f"(assert (<= {sum_expr} 2))\n")
                if add_implied_exact_counts:
                    f.write(f"(assert (>= {sum_expr} 1))\n")

            if add_implied_exact_counts:
                # exactly one period has count == 1
                ones = " ".join([f"(ite (= {sum_exprs[p]} 1) 1 0)" for p in range(P)])
                f.write(f"(assert (= (+ {ones}) 1))\n")
                # total counts sum to W
                totals = " ".join(sum_exprs)
                f.write(f"(assert (= (+ {totals}) {W}))\n")

        # Symmetry breaking: name periods by fixing week 0 diagonally
        # per_{0,m} = m
        if use_sym:
            for m in range(P):
                f.write(f"(assert (= {per_var(0,m)} {m}))\n")

        # Optional extra SB: pin team1 match to period 0 for first k weeks
        if add_team1_pins > 0:
            k = min(add_team1_pins, W)
            for w in range(k):
                m = match_of[w][1]
                f.write(f"(assert (= {per_var(w,m)} 0))\n")

        # Fairness
        if max_diff is not None:
            if not with_home:
                raise ValueError("max_diff requires with_home=True")

            # Break global flip symmetry for home bits 
            if fix_home_sym:
                f.write(f"(assert {home_var(0,0)})\n")

            for t in range(1, n + 1):
                terms = []
                for w in range(W):
                    m = match_of[w][t]
                    a, b = weeks[w][m]
                    if t == a:
                        terms.append(f"(ite {home_var(w,m)} 1 0)")
                    else:
                        terms.append(f"(ite {home_var(w,m)} 0 1)")
                sum_expr = f"(+ {' '.join(terms)})"
                f.write(f"(assert (<= (- (* 2 {sum_expr}) {W}) {max_diff}))\n")
                f.write(f"(assert (<= (- {W} (* 2 {sum_expr})) {max_diff}))\n")

        # Solve
        f.write("(check-sat)\n")

        all_vars = [per_var(w, m) for w in range(W) for m in range(P)]
        if with_home:
            all_vars += [home_var(w, m) for w in range(W) for m in range(P)]

        
        f.write("(get-value (")
        f.write(" ".join(all_vars))
        f.write("))\n")
        f.write("(exit)\n")

    return out_path, weeks, W, P
