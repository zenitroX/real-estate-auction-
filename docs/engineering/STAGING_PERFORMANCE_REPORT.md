# SKANDX Staging Performance & Scalability Benchmark Report

**Document ID:** `ENG-PERF-009`  
**Classification:** Empirical Load Benchmark & Bottleneck Diagnosis  
**Evaluation Date:** November 2026  
**Auditor:** Principal Production Reliability Engineer  

---

## 1. Executive Summary & Benchmark Scope

This benchmark report evaluates the empirical performance of the SKANDX backend under concurrent synthetic load across concurrency levels $C=1, 10, 25, 50$.

All requests were executed against real TCP sockets on the live application server using `ThreadPoolExecutor` in `scripts/test_staging_operations.py`.

- **Peak Measured Throughput:** **$179.4\text{ req/s}$** (`/api/health` at $C=10$)
- **Cached Auction Throughput:** **$127.4\text{ req/s}$** (`/api/auctions` at $C=10$)
- **Memory Consumption:** **$31.2\text{--}32.2\text{ MB}$ RSS** (No memory leak across load cycles)
- **Overall Performance Verdict:** **`VERIFIED`** for staging and single-instance canary traffic. High concurrency ($C \ge 50$) exhibits expected GIL queueing delay.

---

## 2. Empirical Benchmark Data

### 2.1 Health Check Endpoint (`/api/health`)
*Total Requests per Run: 100*

| Concurrency ($C$) | Duration (s) | Throughput (req/s) | Latency $p50$ (ms) | Latency $p95$ (ms) | Latency $p99$ (ms) | Error Rate (%) | CPU (%) | RSS Memory (MB) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$C=1$** | 0.887 | 112.8 | 3.6 | 23.0 | 28.1 | 0.0% | 12.5% | 31.2 |
| **$C=10$** | 0.557 | **179.4** | 7.3 | 518.7 | 527.0 | 0.0% | 35.2% | 31.5 |
| **$C=25$** | 0.631 | 158.4 | 19.4 | 517.8 | 521.0 | 0.0% | 42.0% | 31.7 |
| **$C=50$** | 1.138 | 87.9 | 42.2 | 534.0 | **1,013.2** | 0.0% | 38.0% | 32.0 |

### 2.2 Cached Auction Listings (`/api/auctions`)
*Total Requests per Run: 75*

| Concurrency ($C$) | Duration (s) | Throughput (req/s) | Latency $p50$ (ms) | Latency $p95$ (ms) | Latency $p99$ (ms) | Error Rate (%) | CPU (%) | RSS Memory (MB) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$C=1$** | 0.686 | 109.4 | 6.4 | 24.2 | 27.9 | 0.0% | 15.0% | 31.8 |
| **$C=10$** | 0.589 | **127.4** | 30.0 | 510.7 | 528.6 | 0.0% | 32.0% | 32.1 |
| **$C=25$** | 0.664 | 112.9 | 41.6 | 544.8 | 552.7 | 0.0% | 36.5% | 32.2 |

---

## 3. Bottleneck Analysis & Profiling

```
Throughput (req/s) vs Concurrency
  200 |              * (179.4 req/s @ C=10)
  150 |   * (112.8)        * (158.4 req/s @ C=25)
  100 |                                    * (87.9 req/s @ C=50)
   50 |
    0 +---------------------------------------------
         C=1        C=10         C=25         C=50
```

### 3.1 Root Cause of High-Concurrency Latency ($p99 > 1,000\text{ ms}$)
1. **OS Thread Creation Overheads:** Python's standard `ThreadingHTTPServer` spawns a dedicated operating system thread for each incoming connection (`threading.Thread.start()`). Spawning 50 concurrent OS threads on Windows incurs measurable kernel scheduler overhead.
2. **Global Interpreter Lock (GIL) Contention:** The default Python GIL switch interval is $5\text{ms}$ (`sys.getswitchinterval() = 0.005`). When 50 threads compete for CPU time slices, the 50th connection waits in the CPU run-queue, generating a long-tail $p99$ of $\approx 1,013\text{ms}$.
3. **Memory Stability:** RSS memory remained virtually flat ($\Delta < 1\text{MB}$ across 475 requests), disproving any memory leak or buffer exhaustion hypothesis.

---

## 4. Scalability Recommendations & Production Gate

| Deployment Phase | Traffic Target | Architecture Fit | Required Action |
| :--- | :--- | :--- | :--- |
| **Staging** | $\le 50\text{ req/s}$ | **100% Sufficient** | Deploy as-is with in-memory caching and locks. |
| **Canary Launch** | $\le 100\text{ req/s}$ | **100% Sufficient** | Deploy single container replica behind Nginx. |
| **Public Production Scale** | $> 250\text{ req/s}$ | **Migration Needed** | Migrate runtime to ASGI/WSGI (Uvicorn / Gunicorn with `uvloop`) or place Nginx keepalive connection pool in front. |
