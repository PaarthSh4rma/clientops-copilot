import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


def generate_grounded_answer(
    question: str,
    retrieved_chunks: list[dict],
) -> str:
    context = "\n\n".join(
        [
            f"[Chunk {chunk['chunk_index']}]\n{chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    prompt = f"""
You are an AI assistant answering questions ONLY using the provided document context.

If the answer is not contained in the context, say:
"I could not find the answer in the uploaded document."

Document Context:
{context}

Question:
{question}

Answer:
"""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "system",
                "content": "You are a grounded document QA assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or "No response generated."