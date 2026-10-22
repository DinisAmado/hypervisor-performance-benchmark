import sys
import pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else "resultados_benchmark.csv"
METRICAS = {"CPU_Events_s": "CPU (ev/s)", "RAM_MiB_s": "RAM (MiB/s)",
            "Disk_IOPS": "Disco (IOPS)", "Net_Mbit_s": "Rede (Mbit/s)"}

df = pd.read_csv(CSV)
if "Net_Mbit_s" in df:
    df.loc[df["Net_Mbit_s"] == 0, "Net_Mbit_s"] = float("nan")  # 0.0 = teste ignorado

linhas = []
for (no, amb), g in df.groupby(["Node_ID", "Environment"]):
    for col, nome in METRICAS.items():
        if col not in g:
            continue
        s = g[col].dropna()
        if s.empty:
            continue
        linhas.append({"Node_ID": no, "Ambiente": amb, "col": col, "Metrica": nome,
                       "N": len(s), "Media": s.mean(), "DP": s.std(),
                       "CV_pct": 100 * s.std() / s.mean()})
res = pd.DataFrame(linhas)

base = res[res["Ambiente"] == "Baseline"].set_index(["Node_ID", "col"])["Media"]


def overhead(r):
    chave = (r["Node_ID"], r["col"])
    if chave not in base.index or r["Ambiente"] == "Baseline":
        return float("nan")
    return 100 * (base[chave] - r["Media"]) / base[chave]  


res["Overhead_pct"] = res.apply(overhead, axis=1)
ordem = {"Baseline": 0, "Tipo 1": 1, "Tipo 2": 2}
res = res.sort_values(["Node_ID", "Metrica", "Ambiente"], key=lambda c: c.map(ordem) if c.name == "Ambiente" else c)

res.drop(columns="col").round(2).to_csv("resumo.csv", index=False)

print("\n=== Média ± DP e overhead face ao Baseline (por PC) ===")
for no, g in res.groupby("Node_ID"):
    print(f"\n{no}")
    t = g.assign(Valor=g.apply(lambda r: f"{r['Media']:.2f} ± {r['DP']:.2f}", axis=1))
    print(t[["Metrica", "Ambiente", "Valor", "CV_pct", "Overhead_pct"]].round(2).to_string(index=False))

print("\n=== Comparação entre PCs (média) ===")
print(res.pivot_table(index=["Metrica", "Ambiente"], columns="Node_ID", values="Media").round(2))

with open("tabela_resultados.tex", "w", encoding="utf-8") as f:
    f.write("\\begin{table}[htbp]\n\\centering\n\\caption{Resultados dos benchmarks (média $\\pm$ desvio padrão) e overhead face ao baseline.}\n")
    f.write("\\label{tab:resultados}\n\\begin{tabular}{llllr}\n\\toprule\n")
    f.write("PC & Ambiente & Métrica & Valor & Overhead (\\%) \\\\\n\\midrule\n")
    for _, r in res.iterrows():
        ov = "--" if pd.isna(r["Overhead_pct"]) else f"{r['Overhead_pct']:.1f}"
        no = r["Node_ID"].replace("_", "\\_")
        f.write(f"{no} & {r['Ambiente']} & {r['Metrica']} & ${r['Media']:.1f} \\pm {r['DP']:.1f}$ & {ov} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
print("\nGerados: resumo.csv e tabela_resultados.tex")