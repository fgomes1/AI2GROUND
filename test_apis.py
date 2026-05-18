"""Script rápido para testar conectividade das APIs configuradas no .env"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

results = {}

# ── 1. Testar Supabase ──────────────────────────────────────────
print("=" * 60)
print("1. Testando SUPABASE...")
print("=" * 60)
try:
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Tenta listar tabelas ou fazer um select simples
    response = client.table("ocr_results").select("id").limit(1).execute()
    print(f"   ✅ Supabase OK! Resposta: {response.data}")
    results["supabase"] = "✅ OK"
except Exception as e:
    print(f"   ❌ Supabase FALHOU: {e}")
    results["supabase"] = f"❌ FALHOU: {e}"

# ── 2. Testar Groq ──────────────────────────────────────────────
print()
print("=" * 60)
print("2. Testando GROQ...")
print("=" * 60)
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Responda apenas: OK"}],
        max_tokens=10,
    )
    resposta = completion.choices[0].message.content.strip()
    print(f"   ✅ Groq OK! Modelo respondeu: \"{resposta}\"")
    results["groq"] = "✅ OK"
except Exception as e:
    print(f"   ❌ Groq FALHOU: {e}")
    results["groq"] = f"❌ FALHOU: {e}"

# ── 3. Testar Together AI ───────────────────────────────────────
print()
print("=" * 60)
print("3. Testando TOGETHER AI...")
print("=" * 60)
try:
    import httpx
    resp = httpx.get(
        "https://api.together.xyz/v1/models",
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        timeout=15,
    )
    if resp.status_code == 200:
        models = resp.json()
        count = len(models) if isinstance(models, list) else "?"
        print(f"   ✅ Together AI OK! ({count} modelos disponíveis)")
        results["together"] = "✅ OK"
    else:
        print(f"   ❌ Together AI FALHOU: HTTP {resp.status_code} - {resp.text[:200]}")
        results["together"] = f"❌ HTTP {resp.status_code}"
except Exception as e:
    print(f"   ❌ Together AI FALHOU: {e}")
    results["together"] = f"❌ FALHOU: {e}"

# ── Resumo ──────────────────────────────────────────────────────
print()
print("=" * 60)
print("RESUMO")
print("=" * 60)
for api, status in results.items():
    print(f"   {api.upper():15s} → {status}")
print()
