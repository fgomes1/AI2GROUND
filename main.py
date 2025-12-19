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

# Inicializar Groq
from groq import Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

    # 3. Enviar para a GROQ para OCR
    resultado_ia = {"status": "ia_nao_configurada"}
    
    if groq_client:
        try:
            print(f"DEBUG: Enviando para GROQ: {image_url}")
            completion = groq_client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct", 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": """Você é um especialista em Ciência do Solo e Processamento de Documentos. 
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
                            },
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            # A Groq com json_object já tenta retornar um JSON válido
            import json
            resultado_ia = json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"ERRO GROQ: {str(e)}")
            resultado_ia = {"erro": str(e)}

    # 4. Salvar o registro no Banco de Dados
    data = {
        "user_id": "cdbcbf1c-d8b2-4d1d-82be-43dc7498354e",
        "image_url": image_url,
        "ocr_json": resultado_ia
    }
    
    db_response = supabase.table("ocr_results").insert(data).execute()

    return {
        "mensagem": "Laudo processado com Groq!",
        "url": image_url,
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