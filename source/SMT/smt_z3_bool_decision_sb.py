#!/usr/bin/env python3
import sys, time
from pathlib import Path
from z3 import sat, unsat

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

from io_json import write_result_json
from smt_period_core_bool import build_model

TIME_LIMIT = 300

def extract_schedule(model, weeks, X, n):
    P = n // 2
    W = n - 1
    M = n // 2
    sol = [[None for _ in range(W)] for _ in range(P)]
    for w in range(W):
        for m in range(M):
            for p in range(P):
                if model.evaluate(X[w][m][p], model_completion=True):
                    a, b = weeks[w][m]
                    sol[p][w] = [a, b]
    return sol

def is_full(sol):
    return sol and all(all(c is not None for c in row) for row in sol)

def solve(n, anchor_week=0, timeout_s=300):
    s, weeks, X, home, W, P = build_model(n, use_sym=True, anchor_week=anchor_week, timeout_ms=timeout_s*1000)
    t0 = time.time()
    r = s.check()
    t = time.time() - t0
    if r == sat:
        sol = extract_schedule(s.model(), weeks, X, n)
        return ("sat" if is_full(sol) else "unknown"), sol, t
    if r == unsat:
        return "unsat", [], t
    return "unknown", [], t

if __name__ == "__main__":
    n = int(sys.argv[1])
    aw = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    st, sol, t = solve(n, anchor_week=aw)
    out_dir = Path(__file__).resolve().parents[2] / "res" / "SMT"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{n}.json"
    key = f"SMT_Z3_BOOL_DECISION_SB_aw{aw}"
    write_result_json(key, str(out_path), min(t, TIME_LIMIT), "sat" if st=="sat" else "timeout", sol, obj=None)
    print(f"[{key}] n={n} status={st} time={t:.3f}s")
