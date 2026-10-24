import pandas as pd
import glob

# Lê todos os ficheiros CSV que comecem por "metricas_"
ficheiros = glob.glob("metricas_*.csv")
df_total = pd.concat([pd.read_csv(f) for f in ficheiros])

# Guarda tudo no ficheiro que o teu analyze.py espera
df_total.to_csv("resultados_benchmark.csv", index=False)
print("Ficheiros unidos com sucesso em resultados_benchmark.csv!")