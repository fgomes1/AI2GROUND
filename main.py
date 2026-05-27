from fastapi import FastAPI, UploadFile, File, Depends
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
print(f"DEBUG: Caminho atual: {os.getcwd()}")
print(f"DEBUG: URL encontrada: {os.getenv('SUPABASE_URL')}")

# Pegar variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("As variáveis SUPABASE_URL e SUPABASE_KEY são obrigatórias no arquivo .env")

# Conexão com Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Inicializa o conversor do Docling globalmente para aproveitar cache de modelos de IA
try:
    from docling.document_converter import DocumentConverter
    docling_converter = DocumentConverter()
except ImportError:
    docling_converter = None
    print("AVISO: Docling não está instalado ou falhou ao inicializar.")

# Configuração de CORS para permitir que o Frontend (Vite) acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, coloque a URL do seu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/processar-laudo")
async def processar_laudo(file: UploadFile = File(...)):
    import uuid
    import time
    
    # 1. Upload para o Supabase Storage (com nome único para evitar erro de duplicata)
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    file_path = f"testes/{file_id}.{file_extension}"
    file_content = await file.read()

    supabase.storage.from_("laudos").upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": file.content_type}
    )

    # 2. Gerar a URL pública da imagem
    image_url = supabase.storage.from_("laudos").get_public_url(file_path)

    # Executar OCR Especializado com Docling usando a URL do Supabase
    docling_text = ""
    if docling_converter:
        try:
            print(f"DEBUG: Processando imagem no Docling (isso pode levar alguns segundos)...")
            start_docling = time.time()
            result = docling_converter.convert(image_url)
            docling_text = result.document.export_to_markdown()
            tempo_docling = round(time.time() - start_docling, 2)
            print(f"DEBUG: Extração do Docling concluída com sucesso em {tempo_docling}s.")
        except Exception as e:
            print(f"ERRO DOCLING: {str(e)}")

    # 3. Enviar para Groq para OCR com Llama 4 Scout
    resultado_ia = {"status": "ia_nao_configurada"}
    
    if GROQ_API_KEY:
        try:
            print(f"DEBUG: Enviando para Groq: {image_url}")
            import httpx
            import json
            
            prompt_texto = """Você é um especialista em Ciência do Solo e Processamento de Documentos. 
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
            
            if docling_text:
                prompt_texto += f"\n\n=== TEXTO EXTRAÍDO DO DOCLING ===\n{docling_text}\n=================================\nConsidere os dados acima para preencher o JSON com alta precisão, pois eles vêm de um OCR especializado. A imagem serve para validação visual adicional."

            from groq import AsyncGroq
            groq_client = AsyncGroq(api_key=GROQ_API_KEY)
            
            start_llm = time.time()
            completion = await groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only API. You must ALWAYS respond with a single valid JSON object. No explanations, no markdown, no extra text. Just the raw JSON object."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_texto},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            tempo_llm = round(time.time() - start_llm, 2)
            
            token_usage = {}
            if hasattr(completion, "usage") and completion.usage:
                token_usage = {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                }
            
            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                print(f"DEBUG: Resposta bruta da API:\n{content}")

                # Extrair o primeiro bloco JSON da resposta usando regex
                # (funciona mesmo se o modelo adicionar texto ou markdown ao redor)
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        resultado_ia = json.loads(json_match.group())
                    except json.JSONDecodeError as je:
                        print(f"ERRO: JSON encontrado mas inválido: {je}")
                        resultado_ia = {"erro": "JSON malformado na resposta da IA", "texto_bruto": content}
                else:
                    print(f"ERRO: Nenhum JSON encontrado na resposta:\n{content}")
                    resultado_ia = {"erro": "A IA não retornou um JSON válido", "texto_bruto": content}
            else:
                resultado_ia = {"erro": "Resposta inesperada da API", "detalhes": data}

        except Exception as e:
            print(f"ERRO OPENROUTER: {str(e)}")
            resultado_ia = {"erro": str(e)}

    # 4. Salvar o registro no Banco de Dados
    data = {
        "user_id": "cdbcbf1c-d8b2-4d1d-82be-43dc7498354e",
        "image_url": image_url,
        "ocr_json": resultado_ia
    }
    
    db_response = supabase.table("ocr_results").insert(data).execute()

    # 5. Salvar métricas em CSV local para o TCC
    import os
    import csv
    from datetime import datetime

    csv_filename = "metricas_experimento.csv"
    file_exists = os.path.isfile(csv_filename)
    
    t_doc = tempo_docling if 'tempo_docling' in locals() else 0.0
    t_llm = tempo_llm if 'tempo_llm' in locals() else 0.0
    
    p_tokens = token_usage.get("prompt_tokens", 0) if 'token_usage' in locals() else 0
    c_tokens = token_usage.get("completion_tokens", 0) if 'token_usage' in locals() else 0
    tot_tokens = token_usage.get("total_tokens", 0) if 'token_usage' in locals() else 0

    with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['data_hora', 'id_arquivo', 'tempo_docling_segundos', 'tempo_llm_segundos', 'prompt_tokens', 'completion_tokens', 'total_tokens']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()  # Escreve o cabeçalho se o arquivo for novo
            
        writer.writerow({
            'data_hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'id_arquivo': file_id,
            'tempo_docling_segundos': t_doc,
            'tempo_llm_segundos': t_llm,
            'prompt_tokens': p_tokens,
            'completion_tokens': c_tokens,
            'total_tokens': tot_tokens
        })

    return {
        "mensagem": "Laudo processado com Groq!",
        "url": image_url,
        "metricas": {
            "tempo_docling_segundos": tempo_docling if 'tempo_docling' in locals() else None,
            "tempo_llm_segundos": tempo_llm if 'tempo_llm' in locals() else None,
            "uso_tokens": token_usage if 'token_usage' in locals() else None
        },
        "analise_ia": resultado_ia,
        "db_data": db_response.data
    }

@app.get("/historico/{user_id}")
async def get_historico(user_id: str):
    try:
        # Busca todas as análises de um usuário específico, ordenando pelas mais recentes
        response = supabase.table("ocr_results").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"ERRO HISTORICO: {str(e)}")
        return {"erro": str(e)}

@app.put("/atualizar-laudo/{id}")
async def atualizar_laudo(id: str, data: dict):
    try:
        # Atualiza apenas os dados do OCR para o ID específico
        response = supabase.table("ocr_results").update({"ocr_json": data}).eq("id", id).execute()
        return {"mensagem": "Laudo atualizado com sucesso!", "data": response.data}
    except Exception as e:
        print(f"ERRO AO ATUALIZAR: {str(e)}")
        return {"erro": str(e)}