# benchmark.py
"""
Non-invasive benchmarking toolkit.
Use it to wrap existing functions, blocks, or the whole FastAPI app
without editing any of your source files.

Dependencies: psutil (already in your requirements.txt).
"""
import os
import gc
import time
import tracemalloc
import statistics
from contextlib import contextmanager
from functools import wraps
from typing import Callable

import psutil

_PROCESS = psutil.Process(os.getpid())


# ---------- low level ----------

def rss_mb() -> float:
    """Resident Set Size of this process, in MB."""
    return _PROCESS.memory_info().rss / 1024 / 1024


def _slope(values):
    """Least-squares slope (units of y per iteration)."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, values))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


# ---------- context manager ----------

@contextmanager
def timer(label: str = "block", trace: bool = True):
    """
    Wall-clock + RSS + (optional) tracemalloc peak for a with-block.

        with timer("my step"):
            do_stuff()
    """
    gc.collect()
    rss_before = rss_mb()
    if trace:
        tracemalloc.start()
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt_ms = (time.perf_counter() - t0) * 1000
        peak_kb = 0.0
        if trace:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak_kb = peak / 1024
        rss_after = rss_mb()
        print(
            f"[TIMER] {label:<45} "
            f"time={dt_ms:8.2f} ms | "
            f"py_peak={peak_kb:9.1f} KB | "
            f"rss {rss_before:7.2f} -> {rss_after:7.2f} MB "
            f"(Δ{rss_after - rss_before:+.3f})"
        )


# ---------- decorator (single call) ----------

def timed(label: str | None = None, trace: bool = True):
    """Decorator: log one call of the wrapped function."""
    def deco(fn):
        name = label or f"{fn.__module__}.{fn.__name__}"
        @wraps(fn)
        def wrapper(*a, **k):
            with timer(name, trace=trace):
                return fn(*a, **k)
        return wrapper
    return deco


# ---------- repeat-and-profile (leak detector) ----------

def profile(func: Callable, *args, iterations: int = 10, warmup: int = 2,
            label: str | None = None, **kwargs):
    """
    Run `func` several times and report timing stats + RSS growth.

    A cheap leak heuristic: after warmup, fit a line to RSS vs iteration.
    If the slope is clearly positive (say > 0.1 MB/iter) it *might* be a leak
    (usually a connection or buffer not being closed).
    """
    name = label or getattr(func, "__name__", str(func))

    for _ in range(warmup):
        func(*args, **kwargs)

    gc.collect()
    rss_start = rss_mb()

    times_ms = []
    rss_track = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        func(*args, **kwargs)
        times_ms.append((time.perf_counter() - t0) * 1000)
        rss_track.append(rss_mb())

    gc.collect()
    rss_end = rss_mb()
    growth = rss_end - rss_start
    slope = _slope(rss_track)

    print(f"\n=== PROFILE: {name} ===")
    print(f"  iterations        : {iterations} (+{warmup} warmup)")
    print(f"  time (ms)         : min={min(times_ms):.2f}  "
          f"max={max(times_ms):.2f}  "
          f"mean={statistics.mean(times_ms):.2f}  "
          f"median={statistics.median(times_ms):.2f}")
    if len(times_ms) > 1:
        print(f"  time stdev (ms)   : {statistics.stdev(times_ms):.2f}")
    print(f"  RSS start/end     : {rss_start:.2f} / {rss_end:.2f} MB "
          f"(total Δ{growth:+.2f} MB)")
    print(f"  RSS slope         : {slope:+.4f} MB / iteration")
    verdict = "POSSIBLE LEAK" if slope > 0.1 else "looks stable"
    print(f"  verdict           : {verdict}")

    return {
        "name": name,
        "times_ms": times_ms,
        "rss_start_mb": rss_start,
        "rss_end_mb": rss_end,
        "growth_mb": growth,
        "slope_mb_per_iter": slope,
    }


# ---------- tracemalloc diff (real allocation sites) ----------

def tracemalloc_diff(func: Callable, *args, iterations: int = 10,
                     top: int = 10, label: str | None = None, **kwargs):
    """
    Uses tracemalloc snapshot diffing to find *where* memory is being
    allocated between two runs. Best tool for finding the actual leak line.
    """
    name = label or getattr(func, "__name__", str(func))
    for _ in range(2):
        func(*args, **kwargs)  # warmup

    gc.collect()
    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()

    for _ in range(iterations):
        func(*args, **kwargs)

    gc.collect()
    snap2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    diff = snap2.compare_to(snap1, "lineno")
    print(f"\n=== TRACEMALLOC DIFF: {name} "
          f"({iterations} iterations) ===")
    for stat in diff[:top]:
        print(f"  {stat}")
    return diff


# ---------- ASGI middleware for FastAPI ----------

class BenchmarkMiddleware:
    """
    ASGI middleware. Attach in a launcher file — main.py stays untouched.

        from main import app
        from benchmark import BenchmarkMiddleware
        app.add_middleware(BenchmarkMiddleware)
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        gc.collect()
        rss0 = rss_mb()
        t0 = time.perf_counter()
        status = {"code": None}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000
            rss1 = rss_mb()
            print(
                f"[REQ] {scope['method']:<4} {scope['path']:<30} "
                f"-> {status['code']} | {dt_ms:8.1f} ms | "
                f"rss {rss0:7.2f} -> {rss1:7.2f} MB "
                f"(Δ{rss1 - rss0:+.3f})"
            )