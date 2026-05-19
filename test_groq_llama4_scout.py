import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Buscando modelos disponíveis na Groq...")
try:
    models = client.models.list()
    available = [m.id for m in models.data]

    print("Modelos contendo 'llama':")
    for m in available:
        if 'llama' in m.lower():
            print(" -", m)

    # Procurando Llama 4 Scout
    scout_models = [m for m in available if 'scout' in m.lower() or 'llama-4' in m.lower()]
    print(f"\nModelos Scout / Llama 4 encontrados: {scout_models}")

    model_to_use = "llama-4-scout-17b-16e-instruct" # Fallback
    if scout_models:
        model_to_use = scout_models[0]

    print(f"\n=====================================")
    print(f"Testando chamada para: {model_to_use}")
    print(f"=====================================")

    completion = client.chat.completions.create(
        model=model_to_use,
        messages=[{"role": "user", "content": "Responda apenas: 'Testando Llama 4 Scout no Groq. OK!'"}],
        max_tokens=30,
    )
    resposta = completion.choices[0].message.content.strip()
    print(f"\n✅ SUCESSO na conta gratuita!")
    print(f"Resposta da IA: {resposta}")
    
except Exception as e:
    print(f"\n❌ Erro ao chamar a API: {e}")
