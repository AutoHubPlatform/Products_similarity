import streamlit as st
import psycopg2
import numpy as np
from PIL import Image
import torch
import open_clip
import os
import uuid
import re
import shutil  # Add this import for file and folder removal
from gpt_utils import generate_product_info

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "fruits"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgre")  # <-- use your new password here
}

# Load CLIP model with caching
@st.cache_resource
def load_model():
    # Revert to the old model configuration
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
    return model, preprocess

# Get DB connection
def get_db_conn():
    print("DB config being used:", DB_CONFIG)  # Debug print to show all DB params
    # Extra debug: print each value separately
    print("Host:", DB_CONFIG["host"])
    print("Port:", DB_CONFIG["port"])
    print("DB Name:", DB_CONFIG["dbname"])
    print("User:", DB_CONFIG["user"])
    print("Password:", repr(DB_CONFIG["password"]))
    return psycopg2.connect(**DB_CONFIG)

# Insert product into the DB
def insert_product(article_number, product_name, image_path, embedding, barcode=None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO products (article_number, product_name, image_path, embedding, barcode, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, now(), now())
        """,
        (article_number, product_name, image_path, embedding.tolist(), barcode)
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

# Fetch product by barcode
def get_product_by_barcode(barcode):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT article_number, product_name, image_path, embedding FROM products WHERE barcode = %s",
        (barcode,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

# Streamlit UI
st.set_page_config(page_title="Products Image Search", layout="centered")
st.title("🛍️ Products Recognition")

# --- Add this before file upload ---
st.markdown("#### OpenAI API Key (required for GPT features)")
api_key_input = st.text_input(
    "Enter your OpenAI API key",
    type="password",
    value=st.session_state.get("openai_api_key", ""),
    key="openai_api_key_input"
)
if api_key_input:
    st.session_state["openai_api_key"] = api_key_input

# Add guidance for users to upload packaged product images
example_image_path = "/home/hazem-elbatawy/Documents/Packaged Products/images.jpeg"
if os.path.exists(example_image_path):
    st.image(example_image_path, caption="Example: Upload images of products in their packaging.", use_column_width=True)
st.info("Please upload images of products as they appear in their packaging (not opened or loose).")

# Barcode field for future barcode verification support
barcode = st.text_input("Enter barcode/EAN (optional, for future verification)", key="barcode")

uploaded_file = st.file_uploader("Upload a fruit image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    st.write("File uploaded successfully!")  # Debug message
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Encode image with CLIP
    model, preprocess = load_model()
    img_tensor = preprocess(image).unsqueeze(0)
    with torch.no_grad():
        # Normalize the embedding to improve similarity search accuracy
        embedding = model.encode_image(img_tensor).cpu().numpy().flatten()
        embedding = embedding / np.linalg.norm(embedding)

    # Save uploaded image locally
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)  # Create the folder if it doesn't exist
    image_filename = f"{uuid.uuid4().hex}.png"
    image_path = os.path.join(upload_folder, image_filename)
    image.save(image_path)

    # Input metadata
    article_number = st.text_input("Enter article number for this fruit (6–32 chars, A-Z, 0-9, '-')", key="article")
    product_name = st.text_input("Enter product name for this fruit", key="product")
    # barcode field is already above and can be used in the future

    if st.button("Save this fruit to database"):
        article_number = article_number.upper().strip()  # Optional: normalize input
        if not article_number or not product_name:
            st.error("Please enter both article number and product name before saving.")
        elif not re.fullmatch(r"[A-Z0-9-]{6,32}", article_number):
            st.error("Invalid article number! Must be 6–32 characters: A-Z, 0–9, and hyphen (-) only.")
        else:
            insert_product(article_number, product_name.strip(), image_path, embedding, barcode)
            st.success(f"Saved {product_name} (Article: {article_number}) to database!")

    # Add a button to check similarity
    if st.button("Check Similarity"):
        if barcode:
            product = get_product_by_barcode(barcode)
            if product:
                art_num, prod_name, img_path, db_embedding = product
                # Convert db_embedding to a NumPy float array if it's not already
                if isinstance(db_embedding, list) or isinstance(db_embedding, np.ndarray):
                    db_embedding = np.array(db_embedding, dtype=np.float32)
                else:
                    # If it's a string (e.g., from PostgreSQL ARRAY or vector), parse it
                    db_embedding = np.fromstring(
                        db_embedding.strip("[]"), sep=",", dtype=np.float32
                    )
                similarity_score = np.dot(embedding, db_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(db_embedding))
                st.subheader("Barcode Verification Result:")
                st.markdown(f"**{prod_name}** (Article: {art_num}) — Similarity: `{similarity_score:.3f}`")
                if os.path.exists(img_path):
                    st.image(img_path, width=100)
            else:
                st.warning("No product found with this barcode.")
        else:
            results = find_similar(embedding)
            st.subheader("Top 3 Similar Products:")
            if not results:
                st.info("No similar products found in the database.")
            for art_num, prod_name, img_path, dist in results:
                # Only calculate similarity if dist is not None and dist > -1
                if dist is not None and (1 + dist) != 0:
                    similarity_score = 1 / (1 + dist)
                else:
                    similarity_score = 0
                st.markdown(f"**{prod_name}** (Article: {art_num}) — Similarity: `{similarity_score:.3f}`")
                if os.path.exists(img_path):
                    st.image(img_path, width=100)
                else:
                    st.warning(f"Image for article {art_num} is no longer available.")

    # Optionally, use GPT to suggest product info
    if st.button("Suggest Product Info with GPT"):
        openai_api_key = st.session_state.get("openai_api_key")
        if not openai_api_key:
            st.error("OpenAI API key is not set. Please enter your API key above to use GPT features.")
        else:
            try:
                suggestion = generate_product_info(
                    f"Photo of {uploaded_file.name}",
                    api_key=openai_api_key  # Pass the key to the utility
                )
                st.info(f"GPT Suggestion:\n{suggestion}")
            except Exception as e:
                st.error(f"Error generating product info: {e}")

    # Add a button to remove uploaded images
    if st.button("Remove Uploaded Images"):
        try:
            # Iterate through all files in the uploads folder and delete them
            for root, dirs, files in os.walk(upload_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)  # Remove individual files
                        st.info(f"Removed file: {file_path}")
                    except Exception as e:
                        st.warning(f"Could not remove file {file_path}: {e}")
            st.success("All uploaded images have been removed successfully.")
        except Exception as e:
            st.error(f"Error while removing uploaded images: {e}")

