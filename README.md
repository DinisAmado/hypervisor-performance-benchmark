# Hypervisor Performance Benchmark

Empirical evaluation of Type 1 vs. Type 2 virtualization overhead against bare-metal execution, automated with Python.

## Project Structure

```text
.
├── benchmark.py          # Benchmark orchestrator (runs sysbench and fio)
├── analyze_results.py    # Overhead tables and IEEE-ready charts
├── requirements.txt      # Python dependencies for the analysis step
├── resultados_benchmark.csv  # Consolidated results (generated)
└── README.md
```

## 1. Prerequisites (Ubuntu / Debian)

Before running the benchmark on the Host or inside a VM, install the required native benchmarking tools and Git:

```bash
sudo apt update && sudo apt install -y sysbench fio python3 git
```

## 2. How to Run the Benchmark (Member 1 & Member 2)

Clone this repository inside the target environment (Baseline, Type 1 VM, or Type 2 VM) and run the orchestrator:

```bash
git clone https://github.com/SEU_UTILIZADOR/NOME_DO_REPO.git
cd NOME_DO_REPO
sudo python3 benchmark.py
```

> **Note:** `sudo` is recommended so `fio` can bypass the OS cache (`--direct=1`) without permission errors.

Each run appends its results to `resultados_benchmark.csv` with the following columns:

| Column         | Description                                      |
|----------------|--------------------------------------------------|
| `Timestamp`    | Date and time of the run                         |
| `Node_ID`      | Hardware node identifier (e.g. `PC_Membro1`)     |
| `Environment`  | `Baseline`, `Tipo 1` or `Tipo 2`                 |
| `Iteration`    | Repetition number                                |
| `CPU_Events_s` | CPU performance (sysbench events per second)     |
| `RAM_MiB_s`    | Memory throughput (MiB/s)                        |
| `Disk_IOPS`    | 4KB random write performance (fio IOPS)          |

## 3. Data Analysis & Visualization (Member 3)

To generate the IEEE charts and overhead percentage tables from the consolidated `resultados_benchmark.csv`:

```bash
pip install -r requirements.txt
python3 analyze_results.py
```

If `resultados_benchmark.csv` does not exist yet, the script generates mock data so the charts can be tested beforehand. **Delete the mock CSV and images before committing real results.**

### Output

- Summary table in the terminal with the mean per node/environment and the **Overhead (%)** relative to the Baseline
- `chart_cpu.png`: CPU performance comparison
- `chart_ram.png`: RAM throughput comparison
- `chart_disk.png`: Disk random write performance

All charts are exported at 300 DPI, ready to be inserted in the IEEE LaTeX/Word document.

### Overhead formula

```text
Overhead (%) = (Baseline - Environment) / Baseline × 100
```

## 4. Contributing Results

After confirming everything works, remove test files and push:

```bash
git add README.md requirements.txt analyze_results.py
git commit -m "Add README, requirements and IEEE plotting script"
git push
```
