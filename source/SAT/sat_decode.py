#!/usr/bin/env python3
import re

def parse_glucose_solution(output: str):
    """
    Parse Glucose output, collect assignments.
    Returns: dict {var_id: True/False}
    """
    assignments = {}
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("v"):
            continue
        for tok in line.split()[1:]:
            if tok == "0":
                continue
            lit = int(tok)
            assignments[abs(lit)] = (lit > 0)
    return assignments


def decode_schedule(assignments, reverse_var, pairings, n: int):
    """
    Decode CNF model into checker format:

      sol[period][week] = [home, away]

    reverse_var : list mapping var_id -> variable name
    pairings: output of the circle method (weeks[w][m] = (a,b))
    """

    periods = n // 2
    weeks = n - 1
    matches_per_week = n // 2

    sol = [[None for _ in range(weeks)] for _ in range(periods)]

    import re
    pat = re.compile(r"^X_(\d+)_(\d+)_(\d+)$")

    for vid, val in assignments.items():
        if not val:
            continue

        idx = vid - 1
        if idx < 0 or idx >= len(reverse_var):
            continue

        name = reverse_var[idx]
        m = pat.match(name)
        if not m:
            continue

        w = int(m.group(1))
        mi = int(m.group(2))
        p = int(m.group(3))

        if not (0 <= w < weeks and 0 <= mi < matches_per_week and 0 <= p < periods):
            continue

        a, b = pairings[w][mi]

        # fixed orientation: a is home, b is away
        sol[p][w] = [a, b]

    # sanity check- all slots must be filled
    for p in range(periods):
        for w in range(weeks):
            if sol[p][w] is None:
                return None

    return sol
