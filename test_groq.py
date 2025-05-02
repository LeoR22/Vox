from dotenv import load_dotenv
import asyncio
from groq import AsyncGroq
import os

load_dotenv()


api_key = os.getenv("GROQ_API_KEY")
jwt_secret = os.getenv("JWT_SECRET")

async def main():
    # Crear cliente de Groq
    client = AsyncGroq(api_key=api_key)


    stream = await client.chat.completions.create(
        # Parámetros requeridos
        messages=[
            {
                "role": "system",
                "content": "you are a helpful assistant."
            },
            {
                "role": "user",
                "content": "quien creo twitter?",
            }
        ],
        model="llama-3.3-70b-versatile", 
        temperature=0.5,  
        top_p=1,  
        stop=None, 
        stream=True,  
    )

    # Imprimir los resultados incrementales del modelo
    async for chunk in stream:
        print(chunk.choices[0].delta.content, end="")

# Ejecutar el script de manera asincrónica
asyncio.run(main())
