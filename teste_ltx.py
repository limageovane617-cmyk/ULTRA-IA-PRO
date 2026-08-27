from gradio_client import Client

print("==========================================")
print("🎬 TESTE LTX-2.3 — ALEX IA ULTRA")
print("==========================================")

SPACE = "https://lightricks-ltx-2-3.hf.space"

PROMPT = (
    "Uma bola vermelha rolando lentamente sobre "
    "uma mesa de madeira, iluminação cinematográfica, "
    "movimento suave de câmera."
)

print("🔌 Conectando ao LTX-2.3...")

try:
    client = Client(SPACE)

    print("✅ Conectado!")
    print()
    print("📋 Consultando a API...")
    
    client.view_api()

    print()
    print("🎥 Enviando pedido de geração...")
    
    job = client.submit(
        input_image=None,
        prompt=PROMPT,
        duration=1.0,
        enhance_prompt=True,
        seed=0,
        randomize_seed=True,
        height=512,
        width=512,
        api_name="/generate_video"
    )

    print("✅ Pedido enviado!")
    print("⏳ Aguardando o LTX-2.3...")
    print()

    resultado = job.result()

    print("==========================================")
    print("🎉 RESULTADO RECEBIDO!")
    print("==========================================")
    print(resultado)

except Exception as erro:
    print("==========================================")
    print("❌ ERRO NO TESTE")
    print("==========================================")
    print(type(erro).__name__)
    print(erro)
