import streamlit as st
import psycopg2
import numpy as np
from PIL import Image
import torch
import open_clip
import os
import uuid
import re

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "fruits"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres")
}

# Load CLIP model with caching
@st.cache_resource
def load_model():
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
    return model, preprocess

# Get DB connection
def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)

# Insert product into the DB
def insert_product(article_number, product_name, image_path, embedding):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO products (article_number, product_name, image_path, embedding, created_at, updated_at)
        VALUES (%s, %s, %s, %s, now(), now())
        """,
        (article_number, product_name, image_path, embedding.tolist())
    )
    conn.commit()
    cur.close()
    conn.close()

# Find similar products
def find_similar(embedding, top_k=3):
    conn = get_db_conn()
    cur = conn.cursor()
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    cur.execute(
        """
        SELECT article_number, product_name, image_path, embedding <#> %s::vector AS distance
        FROM products
        ORDER BY distance ASC
        LIMIT %s
        """,
        (embedding_str, top_k)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

# Streamlit UI
st.set_page_config(page_title="Fruit Similarity Search", layout="centered")
st.title("🍓 Fruit Similarity Search")

uploaded_file = st.file_uploader("Upload a fruit image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Encode image with CLIP
    model, preprocess = load_model()
    img_tensor = preprocess(image).unsqueeze(0)
    with torch.no_grad():
        embedding = model.encode_image(img_tensor).cpu().numpy().flatten()

    # Save uploaded image locally
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)
    image_filename = f"{uuid.uuid4().hex}.png"
    image_path = os.path.join(upload_folder, image_filename)
    image.save(image_path)

    # Input metadata
    article_number = st.text_input("Enter article number for this fruit (6–32 chars, A-Z, 0-9, '-')", key="article")
    product_name = st.text_input("Enter product name for this fruit", key="product")

    if st.button("Save this fruit to database"):
        article_number = article_number.upper().strip()  # Optional: normalize input
        if not article_number or not product_name:
            st.error("Please enter both article number and product name before saving.")
        elif not re.fullmatch(r"[A-Z0-9-]{6,32}", article_number):
            st.error("Invalid article number! Must be 6–32 characters: A-Z, 0–9, and hyphen (-) only.")
        else:
            insert_product(article_number, product_name.strip(), image_path, embedding)
            st.success(f"Saved {product_name} (Article: {article_number}) to database!")

    # Show top 3 similar products
    results = find_similar(embedding)
    st.subheader("Top 3 Similar Products:")
    for art_num, prod_name, img_path, dist in results:
        st.markdown(f"**{prod_name}** (Article: {art_num}) — Similarity: `{1 - dist:.3f}`")
        st.image(img_path, width=100)
