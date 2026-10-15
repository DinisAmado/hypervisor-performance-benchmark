# Hypervisor Performance Benchmark

Empirical evaluation of Type 1 vs. Type 2 virtualization overhead against bare-metal execution, automated with Python.

## 1. Prerequisites (Ubuntu / Debian)
Before running the benchmark on the Host or inside a VM, install the required native benchmarking tools and Git:

```bash
sudo apt update && sudo apt install -y sysbench fio python3 git
