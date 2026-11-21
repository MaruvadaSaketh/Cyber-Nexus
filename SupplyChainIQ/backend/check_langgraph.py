"""Smoke test for the langgraph / xxhash / langchain stack.

Run from ``SupplyChainIQ/backend``::

    python check_langgraph.py

Exits 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import sys
from typing import TypedDict


class State(TypedDict):
    n: int


def bump(state: State) -> State:
    return {"n": state["n"] + 1}


def main() -> int:
    failures: list[str] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        print(f"{'PASS' if condition else 'FAIL'}  {name}{'' if condition else '  ' + detail}")
        if not condition:
            failures.append(name)

    try:
        import xxhash
    except Exception as exc:  # pragma: no cover
        print(f"FAIL  import xxhash: {type(exc).__name__}: {exc}")
        return 1

    backend = "pure-python" if xxhash.xxh3_128.__module__.endswith("_pure") else "C extension"
    check("xxhash imports", True, "")
    print(f"      backend: {backend}")
    check(
        "xxhash xxh3_128 reference vector",
        xxhash.xxh3_128(b"a").intdigest() == 225219434562328483135862406050043285023,
    )

    try:
        import langchain_core
        import langgraph
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:
        print(f"FAIL  import langgraph: {type(exc).__name__}: {exc}")
        return 1

    check("langgraph imports", True)
    print(f"      langgraph {getattr(langgraph, '__version__', 'n/a')}, langchain-core {langchain_core.__version__}")

    graph = StateGraph(State)
    graph.add_node("bump", bump)
    graph.add_edge(START, "bump")
    graph.add_edge("bump", END)
    result = graph.compile().invoke({"n": 41})
    check("StateGraph runs", result == {"n": 42}, f"got {result}")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
