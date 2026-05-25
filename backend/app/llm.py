import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

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
        You are a grounded AI document assistant.

        Answer the user's question naturally and clearly using ONLY the provided document context.

        Rules:
        - Do not use outside knowledge.
        - Do not quote raw text unless necessary.
        - Prefer concise, natural answers.
        - If the answer names a person, object, policy, date, or number, make that explicit.
        - If the answer is not contained in the context, say:
        "I could not find the answer in the uploaded document."

        Document Context:
        {context}

        Question:
        {question}

        Answer:
        """

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
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