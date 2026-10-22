#!/usr/bin/env python3
"""Benchmark unificado (CPU, RAM, disco, rede) para comparar
Baseline, Hypervisor Tipo 1 e Hypervisor Tipo 2.
Usar EXATAMENTE este script em todos os ambientes e em ambos os PCs."""
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

FICHEIRO_CSV = "resultados_benchmark.csv"
NUM_REPETICOES = 5
PAUSA_S = 3
FICHEIRO_FIO = "teste_io.tmp"

CAMPOS = ["Timestamp", "Node_ID", "Environment", "Hypervisor", "Threads",
          "vCPUs", "RAM_Total_MiB", "Iteration",
          "CPU_Events_s", "RAM_MiB_s", "Disk_IOPS", "Net_Mbit_s"]


def executar(comando, nome):
    res = subprocess.run(comando, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  [Erro em {nome}] {res.stderr.strip()[:200]}")
        return None
    return res.stdout


def teste_cpu(threads):
    saida = executar(["sysbench", "cpu", "--cpu-max-prime=20000",
                      f"--threads={threads}", "--time=10", "run"], "CPU")
    m = re.search(r"events per second:\s+([0-9.]+)", saida or "")
    return float(m.group(1)) if m else None


def teste_ram(threads):
    saida = executar(["sysbench", "memory", "--memory-block-size=1M",
                      "--memory-total-size=10G", f"--threads={threads}", "run"], "RAM")
    m = re.search(r"\(([0-9.]+)\s+MiB/sec\)", saida or "")
    return float(m.group(1)) if m else None


def teste_disco():
    comando = ["fio", "--name=teste_io", f"--filename={FICHEIRO_FIO}",
               "--ioengine=libaio", "--iodepth=1", "--rw=randwrite", "--bs=4k",
               "--direct=1", "--size=256M", "--numjobs=1", "--runtime=10",
               "--time_based", "--output-format=json"]
    try:
        saida = executar(comando, "Disco")
        if not saida:
            return None
        # O fio pode escrever avisos antes do JSON
        dados = json.loads(saida[saida.index("{"):])
        return round(dados["jobs"][0]["write"]["iops"], 2)
    except (ValueError, KeyError, IndexError) as e:
        print(f"  [Erro em Disco] output inesperado: {e}")
        return None
    finally:
        if os.path.exists(FICHEIRO_FIO):
            os.remove(FICHEIRO_FIO)


def teste_rede(ip_servidor):
    saida = executar(["iperf3", "-c", ip_servidor, "-t", "10", "-J"], "Rede")
    if not saida:
        return None
    try:
        bps = json.loads(saida)["end"]["sum_received"]["bits_per_second"]
        return round(bps / 1_000_000, 2)
    except (ValueError, KeyError):
        return None


def ram_total_mib():
    with open("/proc/meminfo") as f:
        for linha in f:
            if linha.startswith("MemTotal"):
                return int(linha.split()[1]) // 1024
    return None


def guardar_linha(linha):
    existe = os.path.exists(FICHEIRO_CSV)
    if existe:
        with open(FICHEIRO_CSV, newline="") as f:
            cabecalho = next(csv.reader(f), [])
        if cabecalho != CAMPOS:
            sys.exit(f"'{FICHEIRO_CSV}' tem um cabeçalho diferente. "
                     "Renomeia ou apaga o ficheiro antigo antes de continuar.")
    with open(FICHEIRO_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if not existe:
            w.writeheader()
        w.writerow(linha)


def correr_ronda(threads, ip_servidor):
    cpu = teste_cpu(threads)
    ram = teste_ram(threads)
    disco = teste_disco()
    rede = teste_rede(ip_servidor) if ip_servidor else None
    return cpu, ram, disco, rede


if __name__ == "__main__":
    print("=== CONFIGURAÇÃO DO BENCHMARK ===")
    print("1 - PC Membro 1\n2 - PC Membro 2")
    pc_id = "PC_Membro1" if input("Escolhe o PC (1 ou 2): ").strip() == "1" else "PC_Membro2"

    print("\n1 - Baseline (Nativo)\n2 - Hypervisor Tipo 1\n3 - Hypervisor Tipo 2")
    ambiente = {"1": "Baseline", "2": "Tipo 1", "3": "Tipo 2"}.get(
        input("Escolhe o Ambiente (1, 2 ou 3): ").strip(), "Desconhecido")

    hypervisor = input("Nome do hypervisor (ex: Proxmox, VirtualBox; ENTER se Baseline): ").strip() or "Nenhum"
    threads = int(input("Nº de threads (IGUAL em todos os ambientes do mesmo PC) [2]: ").strip() or 2)

    ip_servidor = input("IP do servidor iPerf3 (ENTER para ignorar a rede): ").strip()

    vcpus = os.cpu_count()
    ram_mib = ram_total_mib()
    print(f"\nAmbiente: {pc_id} | {ambiente} | {hypervisor} | {vcpus} vCPUs | {ram_mib} MiB RAM | {threads} threads")
    if threads > vcpus:
        print(f"AVISO: {threads} threads > {vcpus} vCPUs disponíveis neste ambiente.")

    print("\n[Aquecimento] ronda descartada...")
    correr_ronda(threads, ip_servidor)
    time.sleep(PAUSA_S)

    print(f"\nA iniciar {NUM_REPETICOES} repetições...\n")
    for i in range(1, NUM_REPETICOES + 1):
        print(f"--- Iteração {i} de {NUM_REPETICOES} ---")
        cpu, ram, disco, rede = correr_ronda(threads, ip_servidor)
        print(f"Resultados -> CPU: {cpu} ev/s | RAM: {ram} MiB/s | Disco: {disco} IOPS | Rede: {rede} Mbit/s")
        guardar_linha({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Node_ID": pc_id, "Environment": ambiente, "Hypervisor": hypervisor,
            "Threads": threads, "vCPUs": vcpus, "RAM_Total_MiB": ram_mib,
            "Iteration": i, "CPU_Events_s": cpu, "RAM_MiB_s": ram,
            "Disk_IOPS": disco, "Net_Mbit_s": rede,
        })
        if i != NUM_REPETICOES:
            time.sleep(PAUSA_S)

    print(f"\nConcluído! Dados guardados em '{FICHEIRO_CSV}'.")