import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_product_info(image_description, api_key=None):
    if api_key is None:
        api_key = openai.api_key  # fallback if set globally
    client = openai.OpenAI(api_key=api_key)
    
    prompt = (
        f"Given the following product image description: '{image_description}', "
        "suggest a product name, category, and a short description."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
