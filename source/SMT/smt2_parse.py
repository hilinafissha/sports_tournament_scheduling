#!/usr/bin/env python3
import re


def parse_status(stdout: str) -> str:
    s = " ".join(stdout.strip().split()).lower()
    toks = re.findall(r"[a-zA-Z_]+", s)
    if "unsat" in toks:
        return "unsat"
    if "sat" in toks:
        return "sat"
    if "unknown" in toks:
        return "unknown"
    return "unknown"


def parse_get_value(stdout: str) -> dict:
    text = " ".join(stdout.split())
    pairs = re.findall(r"\(\s*([A-Za-z0-9_]+)\s+([^\)\s]+)\s*\)", text)
    env = {}
    for name, val in pairs:
        v = val.lower()
        if v == "true":
            env[name] = True
        elif v == "false":
            env[name] = False
        else:
            try:
                env[name] = int(val)
            except Exception:
                env[name] = val
    return env
