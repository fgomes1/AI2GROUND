"""
Gerador de Gráficos para o TCC — Avaliação do LLaMA
=====================================================
Gera 3 visualizações:
  1. Heatmap Angulo x Iluminacao (taxa de acerto de valores)
  2. Matriz por campo de nutriente (quais campos a IA erra)
  3. Gráfico de barras acerto vs erro por condição
"""

import os, sys, json
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# Carrega dados
# ============================================================
df = pd.read_csv("qualidade_experimento.csv")
PASTA_RAIZ = "./dataset_tcc/laudo_14509"
GABARITO_PATH = os.path.join(PASTA_RAIZ, "laudo_solo_14509.json")

with open(GABARITO_PATH, "r", encoding="utf-8") as f:
    gabarito_dados = json.load(f)

def achatar_json(d, prefixo=""):
    itens = {}
    for k, v in d.items():
        chave = f"{prefixo}.{k}" if prefixo else k
        if isinstance(v, dict):
            itens.update(achatar_json(v, chave))
        else:
            itens[chave] = v
    return itens

gabarito_plano = achatar_json(gabarito_dados)

os.makedirs("graficos_tcc", exist_ok=True)

# ============================================================
# GRAFICO 1 — Heatmap Angulo x Iluminacao
# ============================================================
print("Gerando Grafico 1: Heatmap Angulo x Iluminacao...")

# Monta o pivot: Angulo (linhas) x Iluminacao (colunas)
pivot = df.pivot_table(
    index="Angulo",
    columns="Iluminacao",
    values="Acerto_Valores_%",
    aggfunc="mean"
)

# Ordem dos ângulos do melhor para o pior
ordem_angulo = df.groupby("Angulo")["Acerto_Valores_%"].mean().sort_values(ascending=False).index.tolist()
pivot = pivot.reindex(ordem_angulo)

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

sns.heatmap(
    pivot,
    annot=True,
    fmt=".1f",
    cmap=sns.color_palette("RdYlGn", as_cmap=True),
    vmin=0, vmax=100,
    linewidths=1,
    linecolor="#0f172a",
    cbar_kws={"label": "Acerto de Valores (%)", "shrink": 0.8},
    ax=ax,
    annot_kws={"size": 13, "weight": "bold", "color": "#0f172a"}
)

ax.set_title(
    "Heatmap de Acerto — Angulo x Iluminacao",
    fontsize=16, fontweight="bold", color="white", pad=16
)
ax.set_xlabel("Condicao de Iluminacao", fontsize=12, color="#94a3b8", labelpad=8)
ax.set_ylabel("Angulo da Foto", fontsize=12, color="#94a3b8", labelpad=8)
ax.tick_params(colors="white", labelsize=11)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")

cbar = ax.collections[0].colorbar
cbar.ax.yaxis.set_tick_params(color="white")
cbar.ax.tick_params(colors="white")
cbar.set_label("Acerto de Valores (%)", color="white")

plt.tight_layout()
plt.savefig("graficos_tcc/1_heatmap_angulo_iluminacao.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.close()
print("  -> graficos_tcc/1_heatmap_angulo_iluminacao.png")


# ============================================================
# GRAFICO 2 — Matriz por campo de nutriente (qual campo a IA erra)
# ============================================================
print("Gerando Grafico 2: Matriz de acerto por campo de nutriente...")

TOLERANCIA = 0.01  # 1% de tolerância

# Reconstrói a tabela campo x foto (binário: 1=correto, 0=errado)
campos_numericos = {k: v for k, v in gabarito_plano.items() if v is not None and isinstance(v, (int, float))}
nomes_campos = list(campos_numericos.keys())
nomes_fotos = []
matriz_acerto = []

for i in range(1, 17):
    nome_subpasta = f"pasta_{i:03d}"
    caminho_subpasta = os.path.join(PASTA_RAIZ, nome_subpasta)
    if not os.path.exists(caminho_subpasta):
        continue

    arquivos_json = [f for f in os.listdir(caminho_subpasta) if f.endswith(".json")]
    if not arquivos_json:
        continue

    nome_arquivo = arquivos_json[0]
    partes = nome_arquivo.replace(".json", "").split("_")
    angulo = "_".join(partes[1:-2])
    iluminacao = partes[-2]
    label_foto = f"{angulo}\n{iluminacao}"
    nomes_fotos.append(label_foto)

    with open(os.path.join(caminho_subpasta, nome_arquivo), "r", encoding="utf-8") as f:
        extraido = json.load(f)
    extraido_plano = achatar_json(extraido)

    linha = []
    for chave, val_gab in campos_numericos.items():
        val_ext = extraido_plano.get(chave)
        if val_ext is None:
            linha.append(0)
        else:
            try:
                v_gab = float(val_gab)
                v_ext = float(val_ext)
                erro = abs(v_gab - v_ext) / abs(v_gab) if v_gab != 0 else (0.0 if v_ext == 0 else 1.0)
                linha.append(1 if erro <= TOLERANCIA else 0)
            except:
                linha.append(0)
    matriz_acerto.append(linha)

# Limpa os nomes para exibição (remove prefixo categoria)
def nome_curto(chave):
    return chave.split(".")[-1].replace("_", " ").title()

nomes_exibicao = [nome_curto(c) for c in nomes_campos]
df_matriz = pd.DataFrame(matriz_acerto, index=nomes_fotos, columns=nomes_exibicao)

fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

cmap_binario = matplotlib.colors.ListedColormap(["#ef4444", "#22c55e"])

sns.heatmap(
    df_matriz,
    annot=True,
    fmt="d",
    cmap=cmap_binario,
    vmin=0, vmax=1,
    linewidths=0.8,
    linecolor="#0f172a",
    cbar=False,
    ax=ax,
    annot_kws={"size": 10, "weight": "bold", "color": "white"}
)

patch_correto = mpatches.Patch(color="#22c55e", label="Correto (dentro de 1% de tolerancia)")
patch_erro    = mpatches.Patch(color="#ef4444", label="Incorreto / Ausente")
ax.legend(
    handles=[patch_correto, patch_erro],
    loc="upper right",
    fontsize=10,
    facecolor="#1e293b",
    edgecolor="#334155",
    labelcolor="white"
)

ax.set_title(
    "Matriz de Acerto por Campo de Nutriente x Condicao Fotografica",
    fontsize=14, fontweight="bold", color="white", pad=14
)
ax.set_xlabel("Campo do Laudo", fontsize=11, color="#94a3b8", labelpad=8)
ax.set_ylabel("Condicao (Angulo + Iluminacao)", fontsize=11, color="#94a3b8", labelpad=8)
ax.tick_params(colors="white", labelsize=9)
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
plt.xticks(rotation=35, ha="right")
plt.yticks(rotation=0)

# Linha de porcentagem de acerto por coluna (campo)
acerto_por_campo = df_matriz.mean() * 100
for j, pct in enumerate(acerto_por_campo):
    ax.text(j + 0.5, -0.6, f"{pct:.0f}%",
            ha="center", va="center", fontsize=8,
            color="#facc15", fontweight="bold",
            transform=ax.get_xaxis_transform())

plt.tight_layout()
plt.savefig("graficos_tcc/2_matriz_campo_nutriente.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.close()
print("  -> graficos_tcc/2_matriz_campo_nutriente.png")


# ============================================================
# GRAFICO 3 — Barras horizontais: acerto vs erro por foto
# ============================================================
print("Gerando Grafico 3: Barras de acerto vs erro por condicao...")

df_sorted = df.sort_values("Acerto_Valores_%", ascending=True).reset_index(drop=True)
labels = df_sorted.apply(lambda r: f"{r['Angulo']} / {r['Iluminacao']}", axis=1)
acertos = df_sorted["Acerto_Valores_%"]
erros   = 100 - acertos

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

y = range(len(labels))
bars_erro   = ax.barh(y, erros,   color="#ef4444", alpha=0.85, label="Incorreto")
bars_acerto = ax.barh(y, acertos, left=erros, color="#22c55e", alpha=0.85, label="Correto")

# Rótulos de porcentagem dentro da barra
for idx, (a, e) in enumerate(zip(acertos, erros)):
    if a > 5:
        ax.text(e + a/2, idx, f"{a:.0f}%", ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

ax.set_yticks(list(y))
ax.set_yticklabels(labels, fontsize=11, color="white")
ax.set_xlabel("Distribuicao dos Campos (%)", fontsize=12, color="#94a3b8")
ax.set_title(
    "Acerto vs Erro por Condicao Fotografica",
    fontsize=15, fontweight="bold", color="white", pad=14
)
ax.set_xlim(0, 100)
ax.tick_params(colors="white")
ax.xaxis.label.set_color("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_color("#334155")
ax.spines["left"].set_color("#334155")
ax.xaxis.set_tick_params(color="#334155")
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], color="#94a3b8")
ax.axvline(50, color="#64748b", linestyle="--", alpha=0.5, linewidth=1)

legend = ax.legend(
    fontsize=11, loc="lower right",
    facecolor="#1e293b", edgecolor="#334155", labelcolor="white"
)

plt.tight_layout()
plt.savefig("graficos_tcc/3_barras_acerto_por_condicao.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.close()
print("  -> graficos_tcc/3_barras_acerto_por_condicao.png")

print()
print("="*55)
print("Todos os graficos gerados em: graficos_tcc/")
print("="*55)
