# 🏥 AI2GROUND - Processador de Laudos Médicos com IA

Este projeto é uma API de alto desempenho construída com **FastAPI** que automatiza a extração de dados de laudos médicos. Ele utiliza o **Supabase** para armazenamento de arquivos e banco de dados, e a **Groq (Llama 3.2 Vision)** para o processamento inteligente das imagens (OCR).

## 🚀 Funcionalidades

- **Upload de Imagens**: Recebe imagens de laudos médicos (PNG, JPG, etc).
- **Storage Seguro**: Armazena as imagens no Supabase Storage com nomes únicos (UUID).
- **Extração com IA (OCR)**: Utiliza modelos de visão de ponta (Groq) para transformar imagens em dados JSON estruturados.
- **Persistência**: Salva automaticamente o link da imagem e os dados extraídos no PostgreSQL (Supabase).
- **Documentação Automática**: Swagger UI pronto para testes.

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.12+ / FastAPI
- **Banco de Dados & Storage**: Supabase (PostgreSQL)
- **Motor de IA**: Groq Cloud (Modelos Llama 4 Scout / Maverick)
- **Ambiente**: Python-dotenv, Uvicorn

## 📋 Pré-requisitos

Antes de começar, você precisará de:
1. Uma conta no [Supabase](https://supabase.com/) (URL e Key).
2. Uma conta na [Groq Cloud](https://console.groq.com/) (API Key).
3. Python instalado na sua máquina.

## 🔧 Configuração e Instalação

### 1. Clonar o repositório
```bash
git clone <url-do-seu-repositorio>
cd AI2GROUND
```

### 2. Criar e Ativar Ambiente Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:
```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_KEY=sua_chave_anon_ou_service_role
GROQ_API_KEY=sua_chave_da_groq
```

## 🏃 Como Rodar

Inicie o servidor de desenvolvimento:
```bash
uvicorn main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`.

## 🧪 Como Testar

1. Acesse a documentação interativa: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
2. Localize o endpoint `POST /processar-laudo`.
3. Clique em **Try it out** e faça o upload de uma imagem de laudo.
4. Verifique a resposta com os dados extraídos pela IA.

---
Desenvolvido por [Seu Nome/Github] para o desafio AI2GROUND.
