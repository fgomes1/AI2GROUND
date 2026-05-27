"""
Avaliador de Qualidade das Extrações do LLaMA — TCC
=====================================================
Compara os JSONs extraídos pela IA com o gabarito real do laboratório
e gera o arquivo 'qualidade_experimento.csv' com todas as métricas.

Correções em relação ao código original do Gemini:
  1. Nome do gabarito corrigido para 'laudo_solo_14509.json'
  2. Parser do nome do arquivo robusto (aceita nomes com múltiplos '_')
  3. Comparação de VALORES numéricos, não apenas de chaves (erro relativo)
  4. WER/CER aplicado sobre os valores em texto, não sobre todo o JSON serializado
"""

import os
import json
import math
import pandas as pd
from jiwer import wer, cer

# ===========================================================================
# FUNÇÕES DE MÉTRICA
# ===========================================================================

def achatar_json(d, prefixo=""):
    """
    Transforma um JSON aninhado em um dicionário plano.
    Ex: {"quimica": {"ph_agua": 5.65}} → {"quimica.ph_agua": 5.65}
    Isso permite comparar chave por chave, incluindo sub-níveis.
    """
    itens = {}
    for k, v in d.items():
        chave = f"{prefixo}.{k}" if prefixo else k
        if isinstance(v, dict):
            itens.update(achatar_json(v, chave))
        else:
            itens[chave] = v
    return itens


def calcular_metricas_chaves(gabarito_plano, extraido_plano):
    """
    Calcula Precision, Recall, F1 e Accuracy baseado na PRESENÇA das chaves.
    Um True Positive (TP) é uma chave que existe nos dois.
    """
    chaves_gab = set(gabarito_plano.keys())
    chaves_ext = set(extraido_plano.keys())
    universo = chaves_gab.union(chaves_ext)

    tp = len(chaves_gab & chaves_ext)
    fp = len(chaves_ext - chaves_gab)
    fn = len(chaves_gab - chaves_ext)
    tn = len(universo - chaves_gab - chaves_ext)  # chaves que nenhum dos dois tem

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy  = (tp + tn) / len(universo) if len(universo) > 0 else 0.0

    return precision, recall, f1, accuracy


def calcular_acerto_valores(gabarito_plano, extraido_plano, tolerancia=0.01):
    """
    Para cada chave numérica do gabarito, verifica se o valor extraído
    bate com tolerância de 1% (padrão). Retorna:
      - acerto_exato: % de valores idênticos (ou dentro da tolerância)
      - erro_medio_relativo: média do erro percentual nos campos numéricos
    """
    erros_relativos = []
    acertos = 0
    total_numericos = 0

    for chave, val_gab in gabarito_plano.items():
        if val_gab is None:
            continue  # ignora campos nulos no gabarito
        
        try:
            v_gab = float(val_gab)
        except (TypeError, ValueError):
            continue  # ignora campos de texto (ex: data, profundidade)

        total_numericos += 1
        val_ext = extraido_plano.get(chave)

        if val_ext is None:
            erros_relativos.append(1.0)  # 100% de erro: campo ausente
            continue

        try:
            v_ext = float(val_ext)
        except (TypeError, ValueError):
            erros_relativos.append(1.0)
            continue

        if v_gab == 0:
            erro_rel = 0.0 if v_ext == 0 else 1.0
        else:
            erro_rel = abs(v_gab - v_ext) / abs(v_gab)

        erros_relativos.append(min(erro_rel, 1.0))  # limita o erro a 100%

        if erro_rel <= tolerancia:
            acertos += 1

    acerto_exato = acertos / total_numericos if total_numericos > 0 else 0.0
    erro_medio   = sum(erros_relativos) / len(erros_relativos) if erros_relativos else 1.0

    return acerto_exato, erro_medio


def calcular_wer_cer_valores(gabarito_plano, extraido_plano):
    """
    Aplica WER e CER APENAS sobre os valores do gabarito convertidos para texto.
    Isso é mais justo do que serializar o JSON inteiro (que inclui as chaves).
    """
    def valores_para_texto(d):
        partes = []
        for k in sorted(d.keys()):
            v = d.get(k)
            partes.append(str(v) if v is not None else "nulo")
        return " ".join(partes)

    texto_gab = valores_para_texto(gabarito_plano)
    texto_ext = valores_para_texto({k: extraido_plano.get(k) for k in gabarito_plano.keys()})

    v_wer = wer(texto_gab, texto_ext)
    v_cer = cer(texto_gab, texto_ext)
    return round(min(v_wer, 1.0), 4), round(min(v_cer, 1.0), 4)


# ===========================================================================
# CONFIGURAÇÃO DOS CAMINHOS
# ===========================================================================

PASTA_RAIZ_LAUDO = "./dataset_tcc/laudo_14509"

# ✅ CORREÇÃO 1: nome real do arquivo de gabarito
caminho_gabarito = os.path.join(PASTA_RAIZ_LAUDO, "laudo_solo_14509.json")

print(f"📂 Carregando gabarito: {caminho_gabarito}")
with open(caminho_gabarito, "r", encoding="utf-8") as f:
    gabarito_dados = json.load(f)

# Achata o gabarito para comparação plana
gabarito_plano = achatar_json(gabarito_dados)
print(f"✅ Gabarito carregado com {len(gabarito_plano)} campos.")

linhas_estatisticas = []

# ===========================================================================
# LOOP PELAS 16 PASTAS
# ===========================================================================

for i in range(1, 17):
    nome_subpasta = f"pasta_{i:03d}"
    caminho_subpasta = os.path.join(PASTA_RAIZ_LAUDO, nome_subpasta)

    if not os.path.exists(caminho_subpasta):
        print(f"⚠️  Pasta não encontrada: {nome_subpasta}")
        continue

    arquivos_json = [f for f in os.listdir(caminho_subpasta) if f.endswith(".json")]

    if not arquivos_json:
        print(f"⚠️  Nenhum JSON em: {nome_subpasta}")
        continue

    for nome_arquivo in arquivos_json:
        caminho_arquivo = os.path.join(caminho_subpasta, nome_arquivo)
        nome_sem_ext = nome_arquivo.replace(".json", "")
        partes = nome_sem_ext.split("_")

        # ✅ CORREÇÃO 2: Parser robusto para nomes com múltiplos '_'
        # Formato esperado: <laudo>_<angulo>_<iluminacao>_<modelo>
        # Ex: 14509_frontal_sombra_hibrido  → 4 partes ok
        # Ex: 14509_clara_frontal_hibrido   → 4 partes ok
        # Ex: 14509_invertida_flash_hibrido → 4 partes ok
        if len(partes) < 4:
            print(f"⚠️  Nome inesperado (menos de 4 partes): {nome_arquivo} — pulando.")
            continue

        laudo      = partes[0]
        modelo     = partes[-1]          # última parte = modelo
        iluminacao = partes[-2]          # penúltima = iluminação
        angulo     = "_".join(partes[1:-2])  # o que sobra no meio = ângulo

        print(f"   📄 Processando: {nome_arquivo} | ângulo={angulo} ilum={iluminacao} modelo={modelo}")

        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read().strip()

            if not conteudo.startswith("{"):
                extraido_dados = {"texto_bruto": conteudo}
                extraido_plano = {}
            else:
                extraido_dados = json.loads(conteudo)
                extraido_plano = achatar_json(extraido_dados)

            # --- Métricas de ESTRUTURA (presença de chaves) ---
            prec, rec, f1, acc = calcular_metricas_chaves(gabarito_plano, extraido_plano)

            # ✅ CORREÇÃO 3: Métricas de VALORES numéricos
            acerto_val, erro_medio_rel = calcular_acerto_valores(gabarito_plano, extraido_plano)

            # --- WER / CER aplicado nos VALORES, não no JSON inteiro ---
            v_wer, v_cer = calcular_wer_cer_valores(gabarito_plano, extraido_plano)

        except Exception as e:
            print(f"   ❌ Erro ao processar {nome_arquivo}: {e}")
            prec = rec = f1 = acc = acerto_val = 0.0
            erro_medio_rel = 1.0
            v_wer = v_cer = 1.0

        linhas_estatisticas.append({
            "Pasta":              nome_subpasta,
            "Laudo":              laudo,
            "Angulo":             angulo.capitalize(),
            "Iluminacao":         iluminacao.capitalize(),
            "Modelo":             modelo.upper(),
            "Precision_Chaves":   round(prec, 4),
            "Recall_Chaves":      round(rec, 4),
            "F1_Chaves":          round(f1, 4),
            "Accuracy_Chaves":    round(acc, 4),
            "Acerto_Valores_%":   round(acerto_val * 100, 2),  # ex: 85.71 = 85.71% dos campos ok
            "Erro_Medio_Rel_%":   round(erro_medio_rel * 100, 2),
            "WER_Valores":        v_wer,
            "CER_Valores":        v_cer,
        })

# ===========================================================================
# EXPORTA O CSV FINAL
# ===========================================================================

df = pd.DataFrame(linhas_estatisticas)

# Salva na raiz do projeto (onde você roda o script)
df.to_csv("qualidade_experimento.csv", index=False, encoding="utf-8-sig")

print("\n" + "="*60)
print("✅ Análise concluída!")
print(f"   Linhas processadas : {len(df)}")
print(f"   Arquivo gerado     : qualidade_experimento.csv")
print("="*60)

# Mostra um resumo rápido no terminal
if not df.empty:
    print("\n📊 Resumo por Modelo:")
    resumo = df.groupby("Modelo")[["F1_Chaves", "Acerto_Valores_%", "WER_Valores", "CER_Valores"]].mean().round(4)
    print(resumo.to_string())
