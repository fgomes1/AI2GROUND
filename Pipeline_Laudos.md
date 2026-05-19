# Pipeline de Extração de Laudos (OCR + LLM)

**Data**: 18/05/2026
**Projeto**: AI2GROUND

## 📌 Contexto
O objetivo é extrair dados de imagens de laudos de solo (tabelas químicas complexas) e convertê-los em um JSON estruturado para o backend.

---

## 🛠️ Evolução da Arquitetura

### Fase 1: Uso da Groq (Llama 4 Maverick 17B)
* **Como funcionava**: A imagem era enviada diretamente para a API da Groq.
* **Vantagem**: A Groq tem um hardware dedicado muito rápido (LPUs) e suporta o parâmetro `response_format: {"type": "json_object"}` de forma nativa e muito confiável.
* **Motivo dos acertos**: O modelo 17B é inteligente, e a trava de JSON da Groq impedia que a IA respondesse com texto solto ou markdown quebrados.

### Fase 2: Transição para OpenRouter (Llama 3.2 11B Vision)
* **Como funciona**: Mudamos o provedor para o OpenRouter utilizando um modelo de visão menor.
* **Problema encontrado**: A IA começava a retornar texto fora do JSON (ex: "Aqui está seu resultado:" ou marcações ````json`). Isso quebrava o parser (`json.loads()`).
* **Soluções aplicadas**:
  1. Adição de um **System Prompt** rigoroso (`"role": "system"` forçando apenas JSON).
  2. Implementação de **Regex** (`re.search(r'\{[\s\S]*\}')`) no backend para extrair apenas o bloco de chaves `{}` da resposta, ignorando textos adjacentes.
  3. Adição do `response_format` no payload do OpenRouter, que passa a requisição para o provedor subjacente forçar o JSON (igual à Groq).
  4. Adicionamos a captura de `token_usage` (prompt + completion) no retorno da API e gravamos isso no Supabase para auditoria.

---

## 🚀 Próximo Passo Ideal: Pipeline Híbrido (2 Estágios)

Como os laudos são documentos altamente tabulares, confiar em um VLM (Vision-Language Model) genérico para fazer a leitura visual E a estruturação ao mesmo tempo é arriscado. A solução ideal discutida foi:

1. **OCR Especializado (Docling)**
   * **Execução**: Roda localmente (gratuito e sem delay de API).
   * **Função**: Lê a imagem e extrai com precisão as tabelas, mantendo a estrutura original do documento, gerando um formato Markdown confiável.
   
2. **Estruturação JSON (LLM de Texto)**
   * **Execução**: API via Groq ou OpenRouter (usando um modelo forte apenas para texto, como Llama 3.3 70B ou Llama 4).
   * **Função**: Pega o Markdown sujo do Docling e converte perfeitamente para o Schema JSON exigido pelo banco de dados.

**Por que é melhor?** 
Separar a visão (Docling) do raciocínio lógico (LLM Texto) reduz consideravelmente as alucinações e os erros em valores numéricos decimais presentes nas análises de solo.
