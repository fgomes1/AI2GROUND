"""Teste do Llama 3.2 11B Vision via OpenRouter (apirouter)"""
import os
import json
from dotenv import load_dotenv
import httpx

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY não encontrada no .env")
    exit(1)

print("=" * 60)
print("Testando Llama 3.2 11B Vision via OpenRouter")
print("=" * 60)

# Imagem pública de teste (paisagem aleatória)
test_image_url = "https://picsum.photos/id/29/800/600.jpg"

payload = {
    "model": "meta-llama/llama-3.2-11b-vision-instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Descreva o que você vê nesta imagem em 2 frases curtas em português."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": test_image_url}
                }
            ]
        }
    ],
    "max_tokens": 150,
    "temperature": 0.3
}

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "AI2GROUND Test"
}

try:
    print(f"\n📤 Enviando imagem de teste para o modelo...")
    print(f"   Modelo: meta-llama/llama-3.2-11b-vision-instruct")
    print(f"   Imagem: foto de frutas (Wikipedia)\n")

    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    if resp.status_code == 200:
        data = resp.json()
        resposta = data["choices"][0]["message"]["content"]
        model_used = data.get("model", "?")
        usage = data.get("usage", {})

        print(f"✅ SUCESSO!")
        print(f"   Modelo usado: {model_used}")
        print(f"   Tokens: {usage.get('prompt_tokens', '?')} prompt + {usage.get('completion_tokens', '?')} completion")
        print(f"\n📝 Resposta do modelo:")
        print(f"   {resposta}")
    else:
        print(f"❌ FALHOU: HTTP {resp.status_code}")
        print(f"   {resp.text[:500]}")

except Exception as e:
    print(f"❌ ERRO: {e}")
