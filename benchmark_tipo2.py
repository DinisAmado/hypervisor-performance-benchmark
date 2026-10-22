import subprocess
import csv
import json
import re
import time
from datetime import datetime

FICHEIRO_CSV = 'resultados_benchmark.csv'
NUM_REPETICOES = 5

def correr_teste_cpu():
    comando = ["sysbench", "cpu", "--cpu-max-prime=20000", "--threads=4", "--time=10", "run"]
    res = subprocess.run(comando, capture_output=True, text=True)
    if res.returncode != 0: return None
    match = re.search(r"events per second:\s+([0-9.]+)", res.stdout)
    return float(match.group(1)) if match else None

def correr_teste_ram():
    comando = ["sysbench", "memory", "--memory-block-size=1M", "--memory-total-size=10G", "--threads=2", "run"]
    res = subprocess.run(comando, capture_output=True, text=True)
    if res.returncode != 0: return None
    match = re.search(r"\(([0-9.]+)\s+MiB/sec\)", res.stdout)
    return float(match.group(1)) if match else None

def correr_teste_disco():
    comando = [
        "fio", "--name=teste_io", "--ioengine=libaio", "--iodepth=1",
        "--rw=randwrite", "--bs=4k", "--direct=1", "--size=256M",
        "--numjobs=1", "--runtime=10", "--time_based", "--output-format=json"
    ]
    res = subprocess.run(comando, capture_output=True, text=True)
    if res.returncode != 0: return None
    dados = json.loads(res.stdout)
    subprocess.run(["rm", "-f", "teste_io.0.0"], capture_output=True)
    return round(dados['jobs'][0]['write']['iops'], 2)

def correr_teste_rede(ip_servidor):
    """Executa o iperf3 em modo cliente e devolve a largura de banda em Mbit/s."""
    if not ip_servidor: return 0.0
    comando = ["iperf3", "-c", ip_servidor, "-t", "10", "-J"] # -J devolve output em JSON
    res = subprocess.run(comando, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  [Erro de Rede] Não foi possível ligar ao servidor iperf3 no IP {ip_servidor}.")
        return None
    dados = json.loads(res.stdout)
    # Extrair bits por segundo e converter para Megabits por segundo (Mbit/s)
    bps = dados['end']['sum_recieved']['bits_per_second']
    return round(bps / 1_000_000, 2)

def guardar_linha_csv(pc_id, ambiente, iteracao, cpu, ram, disco, rede):
    existe = False
    try:
        with open(FICHEIRO_CSV, 'r'): existe = True
    except FileNotFoundError: pass

    with open(FICHEIRO_CSV, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['Timestamp', 'Node_ID', 'Environment', 'Iteration', 'CPU_Events_s', 'RAM_MiB_s', 'Disk_IOPS', 'Net_Mbit_s'])
        
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([agora, pc_id, ambiente, iteracao, cpu, ram, disco, rede])

if __name__ == "__main__":
    print("=== CONFIGURAÇÃO DO BENCHMARK ===")
    print("1 - PC Membro 1\n2 - PC Membro 2")
    op_pc = input("Escolhe o PC (1 ou 2): ").strip()
    pc_id = "PC_Membro1" if op_pc == "1" else "PC_Membro2"

    print("\n1 - Baseline (Nativo)\n2 - Hypervisor Tipo 1\n3 - Hypervisor Tipo 2")
    op_amb = input("Escolhe o Ambiente (1, 2 ou 3): ").strip()
    mapa_amb = {"1": "Baseline", "2": "Tipo 1", "3": "Tipo 2"}
    ambiente = mapa_amb.get(op_amb, "Desconhecido")

    print("\n[Teste de Rede] Precisa de um servidor iPerf3 a correr noutra máquina (ex: Host).")
    ip_servidor = input("Introduz o IP do servidor iPerf3 (ou ENTER para ignorar teste de rede): ").strip()

    print(f"\nA iniciar {NUM_REPETICOES} repetições para [{pc_id} - {ambiente}]...\n")

    for i in range(1, NUM_REPETICOES + 1):
        print(f"--- Iteração {i} de {NUM_REPETICOES} ---")
        cpu = correr_teste_cpu()
        ram = correr_teste_ram()
        disco = correr_teste_disco()
        rede = correr_teste_rede(ip_servidor) if ip_servidor else 0.0
        
        print(f"Resultados -> CPU: {cpu} ev/s | RAM: {ram} MiB/s | Disco: {disco} IOPS | Rede: {rede} Mbit/s")
        guardar_linha_csv(pc_id, ambiente, i, cpu, ram, disco, rede)
        
        if i != NUM_REPETICOES: time.sleep(3)

    print(f"\nConcluído! Dados guardados em '{FICHEIRO_CSV}'.")
