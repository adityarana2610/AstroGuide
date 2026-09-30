"""Empirical Performance Benchmark for DataLoader (Feature F4).
Measures cold vs warm lookup latency, throughput, and cache efficiency.
"""

import gc
import json
import time
from typing import Dict, Any

from astroguide.utils.data_loader import (
    DataLoader,
    load_json_table,
    load_nakshatras,
    load_nakshatra_table,
    load_gochara_rules,
    load_planet_stones,
    load_remedies,
    load_panchang_reference,
)


def run_benchmark() -> Dict[str, Any]:
    DataLoader.clear_cache()
    gc.collect()

    results = {}
    tables = [
        ("nakshatra_table.json", DataLoader.load_nakshatras),
        ("gochara_rules.json", DataLoader.load_gochara_rules),
        ("planet_stone_colour.json", DataLoader.load_planet_stones),
        ("astrological_remedies.json", DataLoader.load_remedies),
        ("panchang_reference.json", DataLoader.load_panchang_reference),
    ]

    cold_latencies = {}
    warm_latencies = {}
    iterations = 5000

    print("=== STARTING COLD LOAD BENCHMARK ===")
    for table_name, load_fn in tables:
        DataLoader.clear_cache()
        t0 = time.perf_counter()
        data = load_fn()
        t_cold_ms = (time.perf_counter() - t0) * 1000.0
        cold_latencies[table_name] = t_cold_ms
        print(f"Cold read [{table_name}]: {t_cold_ms:.3f} ms")

    print("\n=== STARTING WARM CACHE LOOKUP BENCHMARK (5,000 iterations each) ===")
    for table_name, load_fn in tables:
        # Pre-warm
        _ = load_fn()
        times = []
        t_batch_start = time.perf_counter()
        for _ in range(iterations):
            t0 = time.perf_counter()
            _ = load_fn()
            times.append(time.perf_counter() - t0)
        t_batch_total_s = time.perf_counter() - t_batch_start

        avg_warm_us = (sum(times) / len(times)) * 1_000_000.0
        min_warm_us = min(times) * 1_000_000.0
        max_warm_us = max(times) * 1_000_000.0
        throughput_ops_sec = iterations / t_batch_total_s
        cold_ms = cold_latencies[table_name]
        speedup = (cold_ms * 1000.0) / avg_warm_us

        warm_latencies[table_name] = {
            "avg_warm_us": avg_warm_us,
            "min_warm_us": min_warm_us,
            "max_warm_us": max_warm_us,
            "throughput_ops_sec": throughput_ops_sec,
            "speedup_x": speedup,
        }

        print(
            f"Warm reads [{table_name}]: avg={avg_warm_us:.2f} µs | "
            f"min={min_warm_us:.2f} µs | max={max_warm_us:.2f} µs | "
            f"throughput={throughput_ops_sec:,.0f} ops/sec | "
            f"speedup={speedup:,.1f}x"
        )

    cache_info = DataLoader.get_cache_info()
    print(f"\nFinal Cache Stats: hits={cache_info.hits}, misses={cache_info.misses}, currsize={cache_info.currsize}/{cache_info.maxsize}")

    results["cold_latencies_ms"] = cold_latencies
    results["warm_latencies"] = warm_latencies
    results["cache_info"] = {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "currsize": cache_info.currsize,
        "maxsize": cache_info.maxsize,
    }
    return results


if __name__ == "__main__":
    run_benchmark()
