# Explicação das Extrações em Lote (Pipeline Híbrido)

Este documento descreve como funciona o script `extracao_lote.py`, os modelos utilizados, os arquivos gerados e como as métricas são contabilizadas para o TCC.

## 1. Como Funciona o Pipeline Híbrido

O script foi projetado para automatizar a extração de dados estruturados (JSON) a partir de imagens de laudos de solo. Ele funciona em duas etapas principais para cada foto processada:

1. **Etapa 1: OCR Especializado (Docling)**
   - O Docling lê a imagem localmente e extrai todo o texto e tabelas brutas no formato Markdown.
   - **Vantagem:** Excelente para capturar estruturas e números precisos.
   - **Custo:** Nenhum token (roda local). Custa apenas tempo de CPU/Memória (~3 a 5 segundos por foto).

2. **Etapa 2: LLM Multimodal (LLaMA via Groq)**
   - A API da Groq recebe a imagem original (visão direta) e o texto extraído pelo Docling (contexto no prompt).
   - O modelo cruza essas informações para preencher o JSON alvo com alta precisão.
   - **Custo:** Consome tokens da API (prompt e completion) e tempo de rede.

---

## 2. Modos de Execução do Script

O script possui opções (`flags`) para suportar a comparação de abordagens na monografia:

- **Modo Híbrido (Padrão):** `--modelo hibrido`
  Roda o pipeline completo (Docling + LLaMA). Gera os arquivos `_docling.md` (resultado do OCR) e `_hibrido.json` (resultado final).

- **Modo LLaMA Puro:** `--modelo llama`
  Pula a etapa do Docling. O modelo LLaMA recebe apenas a imagem e um prompt vazio de contexto. Útil para comparar se o Docling realmente melhora a precisão na extração. Gera o arquivo `_llama.json`.

- **Modo Somente MD:** `--somente-md`
  Gera apenas os arquivos `.md` do Docling para pastas que possuem um JSON mas não possuem o OCR salvo. Não chama a Groq (zero gasto de tokens).

---

## 3. O que é Salvo em Cada Pasta

Para cada foto extraída (ex: `14509_frontal_clara.jpg`), o script salva os seguintes arquivos na mesma pasta da imagem:

```text
pasta_001/
├── 14509_frontal_clara.jpg             <- Imagem original
├── 14509_frontal_clara_docling.md      <- (Docling) Texto bruto do OCR
├── 14509_frontal_clara_hibrido.json    <- (Docling + LLaMA) Extração com OCR no contexto
└── 14509_frontal_clara_llama.json      <- (Apenas LLaMA) Extração direta sem OCR (se executado)
```

> **Nota para a Monografia:** O arquivo `.md` é muito útil para análise qualitativa, pois permite comparar os erros do OCR com os erros finais do modelo.

---

## 4. Métricas e o Arquivo CSV

Toda extração (seja modo híbrido ou llama) adiciona uma linha ao arquivo `metricas_extracao_lote.csv`. Este CSV concentra os dados essenciais para análise de viabilidade e custos.

| Coluna | Descrição |
|--------|-----------|
| `tempo_docling_s` | Tempo (em segundos) que o Docling levou para processar a imagem localmente. |
| `tempo_groq_s` | Tempo de resposta (em segundos) da API Groq. |
| `tempo_total_s` | Tempo total desde o início até o arquivo JSON ser salvo. |
| `tokens_prompt` | Quantidade de tokens enviados para a API (inclui a imagem base64 + texto do OCR). |
| `tokens_completion`| Tokens gerados pela IA (a resposta JSON). |
| `tokens_total` | Soma dos tokens. O Docling não tem tokens, este valor é 100% da Groq. |

**Importante sobre Performance:** O modelo do Docling é inicializado e carregado em memória apenas uma vez (no início do script) para evitar o carregamento repetido de pesos a cada foto, economizando cerca de 8 segundos por imagem.

---

## 5. Por que deletamos os laudos 14509 e 14510?

Os JSONs iniciais do laudo 14509 e 14510 foram extraídos de forma diferente:
- **14509:** Pelo frontend Web (tempos longos, sobrecarga do navegador).
- **14510:** Pelo script antigo, carregando o Docling a cada imagem.

Para que a **comparação de tempos de processamento** seja cientificamente justa e válida para a monografia, eles foram deletados e devem ser reprocessados pelo script otimizado final. As métricas de qualidade (F1-score, WER, etc.) não seriam afetadas, mas o tempo por imagem estaria totalmente inflado nesses dois laudos.

---

## 6. Comandos Principais

```bash
# Rodar Híbrido em tudo (Docling + LLaMA)
venv/Scripts/python.exe extracao_lote.py --modelo hibrido

# Rodar apenas um laudo específico no modo Híbrido
venv/Scripts/python.exe extracao_lote.py --modelo hibrido --laudo 14511

# Rodar modo LLaMA Puro (sem Docling) para comparação de qualidade
venv/Scripts/python.exe extracao_lote.py --modelo llama

# Roda o simulador para ver os arquivos pendentes (sem extrair)
venv/Scripts/python.exe extracao_lote.py --modelo hibrido --dry-run
```
