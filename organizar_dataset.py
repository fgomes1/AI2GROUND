"""
Organizador do Dataset do TCC
==============================
Para cada laudo que ainda não tem as 16 pastas:
  1. Cria pasta_001 até pasta_016
  2. Move cada foto (.jpg/.png) para a pasta correspondente ao ângulo+iluminação
  3. Cria o LEIA_ME.txt em cada pasta (igual ao padrão do laudo_14509)
  4. Cria um gabarito vazio para preencher manualmente
"""

import os, shutil, re

# ===========================================================
# Configuração
# ===========================================================
RAIZ_DATASET = "./dataset_tcc"

# Mapeamento fixo: (angulo, iluminacao) -> numero da pasta
MAPA_PASTAS = {
    ("frontal",   "clara"):   "pasta_001",
    ("frontal",   "sombra"):  "pasta_002",
    ("frontal",   "tremida"): "pasta_003",
    ("frontal",   "flash"):   "pasta_004",
    ("esquerda",  "clara"):   "pasta_005",
    ("esquerda",  "sombra"):  "pasta_006",
    ("esquerda",  "tremida"): "pasta_007",
    ("esquerda",  "flash"):   "pasta_008",
    ("direita",   "clara"):   "pasta_009",
    ("direita",   "sombra"):  "pasta_010",
    ("direita",   "tremida"): "pasta_011",
    ("direita",   "flash"):   "pasta_012",
    ("invertida", "clara"):   "pasta_013",
    ("invertida", "sombra"):  "pasta_014",
    ("invertida", "tremida"): "pasta_015",
    ("invertida", "flash"):   "pasta_016",
    # Alias para nomes com typo
    ("clara",     "frontal"): "pasta_001",  # ordem invertida → ainda frontal+clara
    ("invertida", "sombra"):  "pasta_014",
    ("invertidia","sombra"):  "pasta_014",  # typo: invertidia
    ("frotal",    "clara"):   "pasta_001",  # typo: frotal
}

LEIA_ME = {
    "pasta_001": "coloque a foto: Frontal + Clara",
    "pasta_002": "coloque a foto: Frontal + Sombra",
    "pasta_003": "coloque a foto: Frontal + Tremida",
    "pasta_004": "coloque a foto: Frontal + Flash",
    "pasta_005": "coloque a foto: Esquerda + Clara",
    "pasta_006": "coloque a foto: Esquerda + Sombra",
    "pasta_007": "coloque a foto: Esquerda + Tremida",
    "pasta_008": "coloque a foto: Esquerda + Flash",
    "pasta_009": "coloque a foto: Direita + Clara",
    "pasta_010": "coloque a foto: Direita + Sombra",
    "pasta_011": "coloque a foto: Direita + Tremida",
    "pasta_012": "coloque a foto: Direita + Flash",
    "pasta_013": "coloque a foto: Invertido + Clara",
    "pasta_014": "coloque a foto: Invertido + Sombra",
    "pasta_015": "coloque a foto: Invertido + Tremida",
    "pasta_016": "coloque a foto: Invertido + Flash",
}

GABARITO_TEMPLATE = """{
  "metadados": {
    "numero_amostra": null,
    "profundidade": null,
    "data_analise": null
  },
  "quimica": {
    "ph_agua": null,
    "ph_cacl2": null,
    "indice_smp": null,
    "fosforo_p": null,
    "potassio_k": null,
    "calcio_ca": null,
    "magnesio_mg": null,
    "enxofre_s": null,
    "materia_organica": null,
    "aluminio_al": null,
    "h_mais_al": null
  },
  "micronutrientes": {
    "zinco_zn": null,
    "manganes_mn": null,
    "ferro_fe": null,
    "cobre_cu": null,
    "boro_b": null
  },
  "calculados": {
    "soma_bases_sb": null,
    "ctc_ph7": null,
    "saturacao_v_percent": null,
    "saturacao_al_m_percent": null
  }
}
"""

def extrair_angulo_iluminacao(nome_arquivo):
    """
    Tenta extrair o ângulo e iluminação do nome do arquivo.
    Ignora o ID do laudo (primeiro token) e a extensão.
    Retorna (angulo, iluminacao) em lowercase ou (None, None) se não reconhecer.
    """
    nome = os.path.splitext(nome_arquivo)[0].lower()
    partes = nome.split("_")
    
    angulos    = {"frontal", "esquerda", "direita", "invertida",
                  "invertido", "frotal", "invertidia"}
    iluminacoes = {"clara", "sombra", "tremida", "flash"}
    
    angulo_encontrado = None
    ilum_encontrada = None
    
    for p in partes[1:]:  # pula o ID do laudo
        if p in angulos and angulo_encontrado is None:
            angulo_encontrado = p
        elif p in iluminacoes and ilum_encontrada is None:
            ilum_encontrada = p
    
    # Normaliza typos
    if angulo_encontrado == "invertido":
        angulo_encontrado = "invertida"
    if angulo_encontrado == "frotal":
        angulo_encontrado = "frontal"
    if angulo_encontrado == "invertidia":
        angulo_encontrado = "invertida"
    
    return angulo_encontrado, ilum_encontrada

# ===========================================================
# Loop pelos layouts e laudos
# ===========================================================
fotos_nao_mapeadas = []

for layout in sorted(os.listdir(RAIZ_DATASET)):
    caminho_layout = os.path.join(RAIZ_DATASET, layout)
    if not os.path.isdir(caminho_layout): continue

    for laudo in sorted(os.listdir(caminho_layout)):
        caminho_laudo = os.path.join(caminho_layout, laudo)
        if not os.path.isdir(caminho_laudo): continue

        # Extrai o ID numérico do laudo (ex: laudo_14510 -> 14510)
        match = re.search(r'(\d+)', laudo)
        if not match:
            print(f"  [AVISO] Não consegui extrair ID de: {laudo}")
            continue
        laudo_id = match.group(1)

        # Verifica se já tem as 16 pastas
        pastas_existentes = [p for p in os.listdir(caminho_laudo)
                             if os.path.isdir(os.path.join(caminho_laudo, p)) and p.startswith("pasta_")]
        
        if len(pastas_existentes) >= 16:
            print(f"[OK] {layout}/{laudo} — já tem {len(pastas_existentes)} pastas, pulando.")
            continue

        print(f"\n[CRIANDO] {layout}/{laudo} (ID={laudo_id})")

        # 1. Cria todas as 16 pastas com LEIA_ME
        for pasta_num, instrucao in LEIA_ME.items():
            caminho_pasta = os.path.join(caminho_laudo, pasta_num)
            os.makedirs(caminho_pasta, exist_ok=True)
            leia_path = os.path.join(caminho_pasta, "LEIA_ME.txt")
            if not os.path.exists(leia_path):
                with open(leia_path, "w", encoding="utf-8") as f:
                    f.write(instrucao)
            print(f"  [+] {pasta_num}/LEIA_ME.txt")

        # 2. Cria gabarito vazio (se não existir nenhum gabarito)
        gabarito_path = os.path.join(caminho_laudo, f"{laudo_id}_gabarito.json")
        if not os.path.exists(gabarito_path):
            with open(gabarito_path, "w", encoding="utf-8") as f:
                f.write(GABARITO_TEMPLATE)
            print(f"  [+] {laudo_id}_gabarito.json (PREENCHER MANUALMENTE!)")

        # 3. Move as fotos para as pastas corretas
        extensoes_imagem = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
        for arquivo in sorted(os.listdir(caminho_laudo)):
            ext = os.path.splitext(arquivo)[1]
            if ext not in extensoes_imagem:
                continue

            angulo, iluminacao = extrair_angulo_iluminacao(arquivo)

            if angulo is None or iluminacao is None:
                print(f"  [!] Não mapeado: {arquivo} (angulo={angulo}, ilum={iluminacao})")
                fotos_nao_mapeadas.append(f"{layout}/{laudo}/{arquivo}")
                continue

            chave = (angulo, iluminacao)
            pasta_destino = MAPA_PASTAS.get(chave)

            if pasta_destino is None:
                print(f"  [!] Combinação desconhecida: {arquivo} -> {chave}")
                fotos_nao_mapeadas.append(f"{layout}/{laudo}/{arquivo} -> {chave}")
                continue

            # Renomeia o arquivo para o padrão correto ao mover
            ext_lower = ext.lower()
            nome_padrao = f"{laudo_id}_{angulo}_{iluminacao}{ext_lower}"
            destino_final = os.path.join(caminho_laudo, pasta_destino, nome_padrao)

            shutil.move(os.path.join(caminho_laudo, arquivo), destino_final)
            print(f"  [->] {arquivo}  =>  {pasta_destino}/{nome_padrao}")

# ===========================================================
# Relatório final
# ===========================================================
print("\n" + "="*60)
print("ORGANIZACAO CONCLUIDA!")
if fotos_nao_mapeadas:
    print(f"\n[ATENCAO] {len(fotos_nao_mapeadas)} foto(s) nao foram movidas (checar manualmente):")
    for f in fotos_nao_mapeadas:
        print(f"  - {f}")
else:
    print("Todas as fotos foram organizadas com sucesso!")
print("="*60)
