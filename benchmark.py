import subprocess
import csv
import json
import re
import time
from datetime import datetime

CSV_FILE = 'resultados_benchmark.csv'
NUM_RUNS = 5  # Scientific standard to calculate mean and standard deviation

def run_cpu_test():
    """Runs sysbench for CPU and returns events per second."""
    command = ["sysbench", "cpu", "--cpu-max-prime=20000", "--threads=2", "--time=10", "run"]
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    match = re.search(r"events per second:\s+([0-9.]+)", res.stdout)
    return float(match.group(1)) if match else None

def run_ram_test():
    """Runs sysbench for RAM memory and returns throughput in MiB/s."""
    command = [
        "sysbench", "memory", 
        "--memory-block-size=1K", 
        "--memory-total-size=10G", 
        "--threads=2", 
        "run"
    ]
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    # Matches the pattern "(XXXX.XX MiB/sec)"
    match = re.search(r"\(([0-9.]+)\s+MiB/sec\)", res.stdout)
    return float(match.group(1)) if match else None

def run_disk_test():
    """Runs fio for random disk writes and returns IOPS."""
    command = [
        "fio", "--name=teste_io", "--ioengine=libaio", "--iodepth=1",
        "--rw=randwrite", "--bs=4k", "--direct=1", "--size=256M",
        "--numjobs=1", "--runtime=10", "--time_based", "--output-format=json"
    ]
    res = subprocess.run(command, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    data = json.loads(res.stdout)
    # Cleans up the temporary test file immediately after measurement
    subprocess.run(["rm", "-f", "teste_io.0.0"], capture_output=True)
    return round(data['jobs'][0]['write']['iops'], 2)

def save_csv_row(node_id, environment, run_iteration, cpu_val, ram_val, disk_val):
    """Appends a new line of results to the CSV file."""
    file_exists = False
    try:
        with open(CSV_FILE, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Node_ID', 'Environment', 'Iteration', 'CPU_Events_s', 'RAM_MiB_s', 'Disk_IOPS'])
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([now, node_id, environment, run_iteration, cpu_val, ram_val, disk_val])

if __name__ == "__main__":
    print("=== BENCHMARK CONFIGURATION ===")
    print("1 - Member 1 PC\n2 - Member 2 PC")
    opt_pc = input("Select machine (1 or 2): ").strip()
    node_id = "PC_Membro1" if opt_pc == "1" else "PC_Membro2"

    print("\n1 - Baseline (Native Bare-Metal)\n2 - Type 1 Hypervisor\n3 - Type 2 Hypervisor")
    opt_env = input("Select environment (1, 2, or 3): ").strip()
    env_map = {"1": "Baseline", "2": "Tipo 1", "3": "Tipo 2"}
    environment = env_map.get(opt_env, "Unknown")

    print(f"\nStarting {NUM_RUNS} runs for [{node_id} - {environment}]...\n")

    for i in range(1, NUM_RUNS + 1):
        print(f"--- Iteration {i} of {NUM_RUNS} ---")
        cpu = run_cpu_test()
        ram = run_ram_test()
        disk = run_disk_test()
        
        print(f"Results -> CPU: {cpu} ev/s | RAM: {ram} MiB/s | Disk: {disk} IOPS")
        save_csv_row(node_id, environment, i, cpu, ram, disk)
        
        if i != NUM_RUNS:
            time.sleep(3)  # 3-second cooldown between iterations to stabilize I/O

    print(f"\nCompleted! Data saved to '{CSV_FILE}'.")