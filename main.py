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
                            {"type": "text", "text": "Extraia todos os dados deste laudo técnico de análise de solo e retorne APENAS um JSON estruturado. Inclua campos como: ph, materia_organica, fosforo, potassio, calcio, magnesio, textura_solo e interpretacao_geral."},
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