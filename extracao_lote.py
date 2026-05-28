"""
Extração em Lote — Pipeline Híbrido (Docling + LLaMA via Groq)
================================================================
Varra todo o dataset_tcc/, encontra cada foto nas pastas,
roda o pipeline de extração e salva o JSON no mesmo diretório.
Registra métricas de cada extração em 'metricas_extracao_lote.csv'.

Arquivos gerados por foto:
  {LAUDO_ID}_{ANGULO}_{ILUMINACAO}_hibrido.json  -> JSON estruturado (LLaMA)
  {LAUDO_ID}_{ANGULO}_{ILUMINACAO}_docling.md    -> Texto bruto do OCR (Docling)

Colunas do CSV de métricas:
  data_hora, layout, laudo_id, pasta, angulo, iluminacao,
  tempo_docling_s, tempo_groq_s, tempo_total_s,
  tokens_prompt, tokens_completion, tokens_total,
  status, arquivo_json

Uso:
  python extracao_lote.py                    # roda tudo
  python extracao_lote.py --layout layout_01 # só um layout
  python extracao_lote.py --laudo 14510      # só um laudo
  python extracao_lote.py --dry-run          # mostra o que faria sem rodar
"""

import os, sys, json, re, time, base64, argparse, csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

_docling_converter = None  # Sera inicializado sob demanda em main()

GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
RAIZ_DATASET    = "./dataset_tcc"
GROQ_MODEL        = "meta-llama/llama-4-scout-17b-16e-instruct"
PAUSA_ENTRE_FOTOS = 3                # segundos entre chamadas (respeita rate limit)
CSV_METRICAS      = "metricas_extracao_lote.csv"

CABECALHO_CSV = [
    "data_hora", "layout", "laudo_id", "pasta", "angulo", "iluminacao",
    "tempo_docling_s", "tempo_groq_s", "tempo_total_s",
    "tokens_prompt", "tokens_completion", "tokens_total",
    "status", "arquivo_json"
]

# ============================================================
# PROMPT (igual ao main.py)
# ============================================================
PROMPT_EXTRACAO = """Você é um especialista em Ciência do Solo e Processamento de Documentos.
Sua tarefa é extrair dados técnicos de laudos de análise de solo e retornar ESTRITAMENTE um objeto JSON.

REGRAS OBRIGATÓRIAS:
1. Extraia apenas valores numéricos para os resultados químicos.
2. Use o ponto (.) como separador decimal (ex: 4.40 em vez de 4,40).
3. Se um campo não estiver presente na imagem, preencha com null.
4. Não inclua nenhuma explicação, texto introdutório ou markdown (como ```json). Retorne apenas o objeto.
5. Siga exatamente a estrutura de chaves abaixo.

ESTRUTURA ALVO:
{
  "metadados": {
    "numero_amostra": string ou null,
    "profundidade": string ou null,
    "data_analise": string ou null
  },
  "quimica": {
    "ph_agua": float ou null,
    "ph_cacl2": float ou null,
    "indice_smp": float ou null,
    "fosforo_p": float ou null,
    "potassio_k": float ou null,
    "calcio_ca": float ou null,
    "magnesio_mg": float ou null,
    "enxofre_s": float ou null,
    "materia_organica": float ou null,
    "aluminio_al": float ou null,
    "h_mais_al": float ou null
  },
  "micronutrientes": {
    "zinco_zn": float ou null,
    "manganes_mn": float ou null,
    "ferro_fe": float ou null,
    "cobre_cu": float ou null,
    "boro_b": float ou null
  },
  "calculados": {
    "soma_bases_sb": float ou null,
    "ctc_ph7": float ou null,
    "saturacao_v_percent": float ou null,
    "saturacao_al_m_percent": float ou null
  }
}"""

# ============================================================
# FUNÇÕES
# ============================================================

def imagem_para_base64(caminho_imagem: str) -> str:
    """Lê a imagem e converte para base64 (evita precisar do Supabase)."""
    with open(caminho_imagem, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def rodar_docling(caminho_imagem: str) -> tuple:
    """Extrai texto com Docling reutilizando o modelo já carregado.
    Retorna (texto, tempo_segundos)."""
    if _docling_converter is None:
        print("    [Docling] Indisponivel, pulando.")
        return "", 0.0
    try:
        print("    [Docling] Extraindo texto...")
        inicio = time.time()
        result = _docling_converter.convert(caminho_imagem)
        texto = result.document.export_to_markdown()
        tempo = round(time.time() - inicio, 2)
        print(f"    [Docling] OK em {tempo}s ({len(texto)} chars)")
        return texto, tempo
    except Exception as e:
        print(f"    [Docling] Falhou: {e}")
        return "", 0.0


def rodar_groq(caminho_imagem: str, docling_texto: str = "") -> tuple:
    """Envia a imagem para o LLaMA via Groq.
    Retorna (resultado_dict, tempo_s, tokens_prompt, tokens_completion, tokens_total)."""
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)

    # Prepara o prompt (adiciona contexto do Docling se disponível)
    prompt = PROMPT_EXTRACAO
    if docling_texto:
        prompt += (
            f"\n\n=== TEXTO EXTRAÍDO PELO DOCLING (OCR ESPECIALIZADO) ===\n"
            f"{docling_texto}\n"
            f"=======================================================\n"
            f"Use os dados acima para preencher o JSON com alta precisão."
        )

    # Encoda a imagem em base64
    img_b64 = imagem_para_base64(caminho_imagem)
    extensao = Path(caminho_imagem).suffix.lower().replace(".", "")
    mime = f"image/{extensao}" if extensao in {"jpg", "jpeg", "png", "webp"} else "image/jpeg"
    if extensao == "jpg":
        mime = "image/jpeg"

    print(f"    [Groq] Enviando para {GROQ_MODEL}...")
    inicio = time.time()

    for tentativa in range(5):
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only API. Always respond with a single valid JSON object. No explanations, no markdown."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{img_b64}"}
                            }
                        ]
                    }
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            break  # Sucesso, sai do loop
        except Exception as e:
            erro_str = str(e)
            if "429" in erro_str or "rate limit" in erro_str.lower():
                # Tenta extrair o tempo de espera da mensagem de erro
                # Exemplo: "Please try again in 8m19.5648s" ou "in 1m52s"
                espera = 60  # Padrão
                m = re.search(r'try again in (?:(\d+)m)?([\d\.]+)s', erro_str)
                if m:
                    mins = int(m.group(1)) if m.group(1) else 0
                    secs = float(m.group(2))
                    espera = (mins * 60) + secs + 5.0  # Adiciona 5 segundos de margem
                print(f"    [AVISO] Limite da API atingido. Pausando por {espera:.1f}s antes de retomar...")
                time.sleep(espera)
            else:
                raise e
    else:
        # Se esgotar as 5 tentativas
        raise Exception("Falhou apos 5 tentativas por limite de taxa da Groq API.")

    tempo = round(time.time() - inicio, 2)
    content = completion.choices[0].message.content

    tok_prompt = tok_completion = tok_total = 0
    if completion.usage:
        tok_prompt     = completion.usage.prompt_tokens
        tok_completion = completion.usage.completion_tokens
        tok_total      = completion.usage.total_tokens
    print(f"    [Groq] OK em {tempo}s | {tok_total} tokens ({tok_prompt}p + {tok_completion}c)")

    # Extrai o JSON da resposta
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            resultado = json.loads(json_match.group())
            return resultado, tempo, tok_prompt, tok_completion, tok_total
        except json.JSONDecodeError:
            print(f"    [ERRO] JSON inválido na resposta")
            erro = {"erro": "JSON malformado", "texto_bruto": content}
            return erro, tempo, tok_prompt, tok_completion, tok_total
    else:
        print(f"    [ERRO] Nenhum JSON na resposta")
        erro = {"erro": "Sem JSON", "texto_bruto": content}
        return erro, tempo, tok_prompt, tok_completion, tok_total


def registrar_metrica(linha: dict):
    """Adiciona uma linha de métricas no CSV. Cria o arquivo e cabeçalho se não existir."""
    existe = os.path.isfile(CSV_METRICAS)
    with open(CSV_METRICAS, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CABECALHO_CSV)
        if not existe:
            writer.writeheader()
        writer.writerow(linha)


def coletar_trabalho(layout_filtro=None, laudo_filtro=None, modelo="hibrido"):
    """
    Retorna lista de fotos pendentes para o modelo informado.
    modelo="hibrido" -> gera _hibrido.json (Docling + LLaMA)
    modelo="llama"   -> gera _llama.json   (so LLaMA, sem Docling)
    Pula automaticamente fotos que ja tem o JSON do modelo escolhido.
    """
    trabalho = []
    for layout in sorted(os.listdir(RAIZ_DATASET)):
        if layout_filtro and layout != layout_filtro:
            continue
        cl = os.path.join(RAIZ_DATASET, layout)
        if not os.path.isdir(cl): continue

        for laudo in sorted(os.listdir(cl)):
            if laudo_filtro and laudo_filtro not in laudo:
                continue
            cla = os.path.join(cl, laudo)
            if not os.path.isdir(cla): continue

            # Extrai ID numérico do laudo
            match = re.search(r'(\d+)', laudo)
            if not match: continue
            laudo_id = match.group(1)

            for pasta in sorted(os.listdir(cla)):
                cp = os.path.join(cla, pasta)
                if not os.path.isdir(cp) or not pasta.startswith("pasta_"): continue

                fotos = [f for f in os.listdir(cp)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if not fotos: continue

                foto = fotos[0]  # cada pasta tem 1 foto
                nome_sem_ext = os.path.splitext(foto)[0].lower()
                partes = nome_sem_ext.split("_")

                if len(partes) < 3:
                    print(f"  [AVISO] Nome inesperado, pulando: {foto}")
                    continue

                angulo    = partes[-2]
                iluminacao = partes[-1]

                # Nomes dos arquivos de saida
                nome_json    = f"{laudo_id}_{angulo}_{iluminacao}_{modelo}.json"
                nome_md      = f"{laudo_id}_{angulo}_{iluminacao}_docling.md"
                caminho_json = os.path.join(cp, nome_json)
                caminho_md   = os.path.join(cp, nome_md)

                # Pula se já foi extraído
                if os.path.exists(caminho_json):
                    continue

                trabalho.append({
                    "layout":      layout,
                    "laudo":       laudo,
                    "laudo_id":    laudo_id,
                    "pasta":       pasta,
                    "angulo":      angulo,
                    "iluminacao":  iluminacao,
                    "modelo":      modelo,
                    "foto_path":   os.path.join(cp, foto),
                    "json_path":   caminho_json,
                    "nome_json":   nome_json,
                    "md_path":     caminho_md,
                    "nome_md":     nome_md,
                })

    return trabalho


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Extração em lote do pipeline híbrido")
    parser.add_argument("--layout",    help="Filtrar por layout (ex: layout_01)")
    parser.add_argument("--laudo",     help="Filtrar por ID do laudo (ex: 14510)")
    parser.add_argument("--modelo",    choices=["hibrido", "llama"], default="hibrido",
                        help="hibrido=Docling+LLaMA (padrao) | llama=so LLaMA sem Docling")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Mostra o que seria processado sem chamar a API")
    parser.add_argument("--somente-md", action="store_true",
                        help="Gera apenas os .md do Docling para pastas que ja tem JSON mas nao tem .md (sem gastar tokens)")
    args = parser.parse_args()

    if not GROQ_API_KEY and not args.somente_md:
        print("[ERRO] GROQ_API_KEY nao encontrada no .env!")
        sys.exit(1)

    # Carrega Docling apenas quando necessario (hibrido ou somente-md)
    # No modo llama puro, o startup e imediato.
    global _docling_converter
    if args.somente_md or args.modelo == "hibrido":
        print("[INIT] Carregando Docling (OCR)...")
        try:
            from docling.document_converter import DocumentConverter
            _docling_converter = DocumentConverter()
            print("[INIT] Docling carregado com sucesso.")
        except Exception as e:
            _docling_converter = None
            print(f"[INIT] Docling nao disponivel: {e}")
    else:
        print("[INIT] Modo llama — Docling nao sera carregado.")
    print("  EXTRACAO EM LOTE — Pipeline Hibrido (Docling + LLaMA)")
    print("="*60)

    # -------------------------------------------------------
    # MODO --somente-md: gera .md para quem ja tem JSON
    # -------------------------------------------------------
    if args.somente_md:
        print("\n[MODO] Gerando apenas .md do Docling (sem chamar Groq)")
        pendentes_md = []
        for layout in sorted(os.listdir(RAIZ_DATASET)):
            if args.layout and layout != args.layout: continue
            cl = os.path.join(RAIZ_DATASET, layout)
            if not os.path.isdir(cl): continue
            for laudo in sorted(os.listdir(cl)):
                if args.laudo and args.laudo not in laudo: continue
                cla = os.path.join(cl, laudo)
                if not os.path.isdir(cla): continue
                match = re.search(r'(\d+)', laudo)
                if not match: continue
                laudo_id = match.group(1)
                for pasta in sorted(os.listdir(cla)):
                    cp = os.path.join(cla, pasta)
                    if not os.path.isdir(cp) or not pasta.startswith('pasta_'): continue
                    jsons = [f for f in os.listdir(cp) if f.endswith('_hibrido.json')]
                    mds   = [f for f in os.listdir(cp) if f.endswith('_docling.md')]
                    fotos = [f for f in os.listdir(cp) if f.lower().endswith(('.jpg','.jpeg','.png'))]
                    if jsons and not mds and fotos:
                        foto = fotos[0]
                        partes = os.path.splitext(foto)[0].lower().split('_')
                        angulo, iluminacao = partes[-2], partes[-1]
                        nome_md = f"{laudo_id}_{angulo}_{iluminacao}_docling.md"
                        pendentes_md.append({
                            "foto_path": os.path.join(cp, foto),
                            "md_path":   os.path.join(cp, nome_md),
                            "nome_md":   nome_md,
                            "label":     f"{layout}/{laudo}/{pasta}"
                        })

        print(f"Pastas com JSON sem .md: {len(pendentes_md)}")
        if args.dry_run:
            for p in pendentes_md:
                print(f"  {p['label']} -> {p['nome_md']}")
            print("\n[DRY-RUN] Nenhuma chamada feita.")
            return

        for idx, p in enumerate(pendentes_md, 1):
            print(f"\n[{idx}/{len(pendentes_md)}] {p['label']}")
            docling_texto, _ = rodar_docling(p["foto_path"])
            with open(p["md_path"], "w", encoding="utf-8") as f:
                if docling_texto:
                    f.write(f"# Extracao Docling\n")
                    f.write(f"**Arquivo:** {os.path.basename(p['foto_path'])}\n")
                    f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(docling_texto)
                else:
                    f.write("# Extracao Docling\n\n> Docling nao conseguiu extrair texto desta imagem.\n")
            print(f"  [SALVO] {p['nome_md']}")

        print(f"\n{'='*60}")
        print(f"  .md gerados: {len(pendentes_md)}")
        print(f"  Tokens gastos: 0 (so Docling, sem Groq)")
        print(f"{'='*60}")
        return
    # -------------------------------------------------------

    trabalho = coletar_trabalho(args.layout, args.laudo, args.modelo)

    if not trabalho:
        print(f"\nNenhuma foto pendente para modelo '{args.modelo}'. Tudo ja extraido!")
        return

    print(f"\nModelo selecionado : {args.modelo.upper()}")
    if args.modelo == "llama":
        print("Modo              : So LLaMA (sem Docling como contexto)")
    else:
        print("Modo              : Hibrido (Docling + LLaMA)")
    print(f"Fotos pendentes   : {len(trabalho)}")
    for t in trabalho:
        print(f"  {t['layout']}/{t['laudo']}/{t['pasta']} -> {t['nome_json']}")

    if args.dry_run:
        print("\n[DRY-RUN] Nenhuma chamada feita.")
        return

    # O script vai rodar direto sem pedir confirmacao (removido a pedido)

    # Processa cada foto
    erros = []
    for idx, t in enumerate(trabalho, 1):
        print(f"\n[{idx}/{len(trabalho)}] {t['layout']}/{t['laudo']}/{t['pasta']}")
        print(f"  Foto   : {os.path.basename(t['foto_path'])}")
        print(f"  Saída  : {t['nome_json']}")

        inicio_total = time.time()
        status = "ok"
        tok_p = tok_c = tok_t = 0
        t_docling = t_groq = 0.0

        try:
            # 1. Docling — roda APENAS no modo hibrido
            if args.modelo == "hibrido":
                docling_texto, t_docling = rodar_docling(t["foto_path"])

                # Salva o .md do Docling
                with open(t["md_path"], "w", encoding="utf-8") as f:
                    if docling_texto:
                        f.write(f"# Extracao Docling\n")
                        f.write(f"**Arquivo:** {os.path.basename(t['foto_path'])}\n")
                        f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write("---\n\n")
                        f.write(docling_texto)
                    else:
                        f.write("# Extracao Docling\n\n> Docling nao conseguiu extrair texto desta imagem.\n")
                print(f"  [SALVO] {t['nome_md']}")
            else:
                # modo llama: sem Docling, contexto vazio
                docling_texto = ""
                t_docling = 0.0
                print(f"  [Docling] Pulado (modo llama)")

            # 2. Groq LLaMA (visao) — sempre roda
            resultado, t_groq, tok_p, tok_c, tok_t = rodar_groq(t["foto_path"], docling_texto)

            # 3. Salva o JSON na pasta
            with open(t["json_path"], "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)

            if "erro" in resultado:
                status = "erro_json"
            print(f"  [SALVO] {t['nome_json']}")

        except Exception as e:
            print(f"  [ERRO] {e}")
            status = "erro_excecao"
            erros.append({"foto": t["foto_path"], "erro": str(e)})

        # 4. Registra métricas no CSV
        tempo_total = round(time.time() - inicio_total, 2)
        registrar_metrica({
            "data_hora":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "layout":             t["layout"],
            "laudo_id":           t["laudo_id"],
            "pasta":              t["pasta"],
            "angulo":             t["angulo"],
            "iluminacao":         t["iluminacao"],
            "tempo_docling_s":    t_docling,
            "tempo_groq_s":       t_groq,
            "tempo_total_s":      tempo_total,
            "tokens_prompt":      tok_p,
            "tokens_completion":  tok_c,
            "tokens_total":       tok_t,
            "status":             status,
            "arquivo_json":       t["nome_json"],
        })
        print(f"  [CSV] Métrica salva -> {CSV_METRICAS}")

        # Pausa para não estourar o rate limit da Groq
        if idx < len(trabalho):
            print(f"  Aguardando {PAUSA_ENTRE_FOTOS}s...")
            time.sleep(PAUSA_ENTRE_FOTOS)

    # Relatório final
    print("\n" + "="*60)
    print(f"  Processadas : {len(trabalho) - len(erros)}/{len(trabalho)}")
    print(f"  Erros       : {len(erros)}")
    if erros:
        print("\n  Fotos com erro:")
        for e in erros:
            print(f"    {e['foto']} -> {e['erro']}")
    print("="*60)


if __name__ == "__main__":
    main()
