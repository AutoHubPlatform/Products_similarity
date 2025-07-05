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
    "password": os.environ.get("DB_PASSWORD", "postgres")
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

# Find similar products - IMPROVED to show Top 3 with better similarity calculation
def find_similar(embedding, top_k=3, min_similarity=0.0):
    """
    Find the most similar products, always returning top_k results if available
    
    Args:
        embedding: Query embedding vector (can be numpy array, list, or database vector)
        top_k: Number of top similar products to return (default: 3)
        min_similarity: Minimum similarity threshold (default: 0.0 to include all)
    """
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Convert embedding to proper format for database query
    if hasattr(embedding, 'tolist'):
        # If it's a numpy array, convert to list
        embedding_list = embedding.tolist()
    elif isinstance(embedding, list):
        # If it's already a list, use as is
        embedding_list = embedding
    else:
        # If it's from database (might be string or other format), convert to list
        if isinstance(embedding, str):
            # Parse string representation of array
            import ast
            try:
                embedding_list = ast.literal_eval(embedding)
            except:
                # Fallback: assume it's already in the right format
                embedding_list = embedding
        else:
            embedding_list = list(embedding)
    
    # First, get total count to check available products
    cur.execute("SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL")
    total_products = cur.fetchone()[0]
    
    if total_products == 0:
        cur.close()
        conn.close()
        return []
    
    # Adjust top_k if there are fewer products than requested
    actual_limit = min(top_k, total_products)
    
    cur.execute(
        """
        SELECT article_number, product_name, image_path, 
               1 - (embedding <=> %s::vector) as similarity
        FROM products 
        WHERE embedding IS NOT NULL
          AND (1 - (embedding <=> %s::vector)) >= %s
        ORDER BY similarity DESC 
        LIMIT %s
        """,
        (embedding_list, embedding_list, min_similarity, actual_limit)
    )
    results = cur.fetchall()
    
    # If we don't get enough results due to similarity threshold,
    # get the top results regardless of threshold
    if len(results) < actual_limit and min_similarity > 0:
        cur.execute(
            """
            SELECT article_number, product_name, image_path, 
                   1 - (embedding <=> %s::vector) as similarity
            FROM products 
            WHERE embedding IS NOT NULL
            ORDER BY similarity DESC 
            LIMIT %s
            """,
            (embedding_list, actual_limit)
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

# Function to get all uploaded files
def get_uploaded_files(upload_folder):
    if not os.path.exists(upload_folder):
        return []
    files = []
    for root, dirs, filenames in os.walk(upload_folder):
        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(filename)
    return files

# Function to get all products from database
def get_all_products():
    """Get all products from database with file existence validation"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, article_number, product_name, image_path, barcode, 
               created_at, updated_at, 512 as embedding_size
        FROM products 
        ORDER BY created_at DESC
    """)
    all_products = cur.fetchall()
    cur.close()
    conn.close()
    
    # Filter out products whose image files no longer exist
    valid_products = []
    for product in all_products:
        image_path = product[3]  # image_path is at index 3
        if image_path and os.path.exists(image_path):
            valid_products.append(product)
    
    return valid_products

# Function to clean up orphaned database records
def cleanup_orphaned_records():
    """Remove database records where image files no longer exist"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Get all products with image paths
    cur.execute("SELECT id, image_path FROM products WHERE image_path IS NOT NULL")
    products = cur.fetchall()
    
    removed_count = 0
    for product_id, image_path in products:
        if not os.path.exists(image_path):
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            removed_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return removed_count

# Function to get database statistics
def get_database_stats():
    """Get database statistics"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Total products (only count those with existing image files)
    cur.execute("SELECT COUNT(*) FROM products WHERE image_path IS NOT NULL")
    all_products = cur.fetchone()[0]
    
    # Count products with existing image files
    cur.execute("SELECT image_path FROM products WHERE image_path IS NOT NULL")
    image_paths = cur.fetchall()
    
    existing_products = 0
    for (image_path,) in image_paths:
        if os.path.exists(image_path):
            existing_products += 1
    
    # Products with barcodes (only those with existing images)
    cur.execute("""
        SELECT COUNT(*) FROM products 
        WHERE barcode IS NOT NULL AND barcode != '' AND image_path IS NOT NULL
    """)
    products_with_barcodes_total = cur.fetchone()[0]
    
    # Count products with barcodes that have existing image files
    cur.execute("""
        SELECT image_path FROM products 
        WHERE barcode IS NOT NULL AND barcode != '' AND image_path IS NOT NULL
    """)
    barcode_image_paths = cur.fetchall()
    
    products_with_barcodes = 0
    for (image_path,) in barcode_image_paths:
        if os.path.exists(image_path):
            products_with_barcodes += 1
    
    # Recent products (last 24 hours with existing images)
    cur.execute("""
        SELECT image_path FROM products 
        WHERE created_at > NOW() - INTERVAL '24 hours' AND image_path IS NOT NULL
    """)
    recent_image_paths = cur.fetchall()
    
    recent_products = 0
    for (image_path,) in recent_image_paths:
        if os.path.exists(image_path):
            recent_products += 1
    
    cur.close()
    conn.close()
    
    return {
        'total_products': existing_products,
        'products_with_barcodes': products_with_barcodes,
        'recent_products': recent_products,
        'orphaned_records': all_products - existing_products  # Records without files
    }

# Streamlit UI
st.set_page_config(page_title="Products Image Search", layout="wide")
st.title("🛍️ Products Recognition & Similarity Search")

# Sidebar for database statistics
with st.sidebar:
    st.header("📊 Database Statistics")
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        product_count = cur.fetchone()[0]
        st.metric("Total Products", product_count)
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Database connection error: {e}")

# === NEW: Search Similar Products Section ===
st.markdown("---")
st.markdown("### 🔍 Search Similar Products from Database")

# Get all products for selection
try:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, article_number, product_name, image_path, barcode, created_at
        FROM products 
        WHERE embedding IS NOT NULL 
        ORDER BY created_at DESC
    """)
    available_products = cur.fetchall()
    cur.close()
    conn.close()
    
    if available_products:
        # Create selection interface
        search_col1, search_col2 = st.columns([1, 2])
        
        with search_col1:
            st.markdown("#### 📋 Select Reference Product")
            
            # Create product options for dropdown
            product_options = []
            product_map = {}
            
            for product in available_products:
                id, article_number, product_name, image_path, barcode, created_at = product
                # Create display name
                display_name = f"{article_number}"
                if product_name:
                    display_name += f" - {product_name}"
                if barcode:
                    display_name += f" (#{barcode})"
                display_name += f" [{created_at.strftime('%Y-%m-%d')}]"
                
                product_options.append(display_name)
                product_map[display_name] = product
            
            selected_product_name = st.selectbox(
                "Choose a product to find similar items:",
                options=product_options,
                help="Select any product from your database to find similar products"
            )
            
            if selected_product_name:
                selected_product = product_map[selected_product_name]
                
                # Display selected product info
                st.markdown("**Selected Product:**")
                st.write(f"🏷️ **Article:** {selected_product[1]}")
                st.write(f"📦 **Name:** {selected_product[2] or 'N/A'}")
                st.write(f"📱 **Barcode:** {selected_product[4] or 'Not set'}")
                
                # Show selected product image
                if selected_product[3] and os.path.exists(selected_product[3]):
                    try:
                        reference_img = Image.open(selected_product[3])
                        st.image(reference_img, caption="Reference Product", width=200)
                    except Exception as e:
                        st.error(f"Error loading image: {e}")
                else:
                    st.warning("🖼️ Image not available")
        
        with search_col2:
            st.markdown("#### ⚙️ Search Parameters")
            
            # Search parameters
            search_top_k = st.slider("Number of similar products to find:", 1, 10, 3, key="search_top_k")
            search_threshold = st.slider("Similarity threshold:", 0.0, 1.0, 0.0, 0.05, 
                                       help="0.0 = show all results, 1.0 = only exact matches", key="search_threshold")
            
            # Search button
            if st.button("🔎 Find Similar Products", type="primary", key="search_similar"):
                if selected_product_name:
                    selected_id = selected_product[0]
                    
                    # Get embedding for selected product
                    conn = get_db_conn()
                    cur = conn.cursor()
                    cur.execute("SELECT embedding FROM products WHERE id = %s", (selected_id,))
                    embedding_result = cur.fetchone()
                    cur.close()
                    conn.close()
                    
                    if embedding_result and embedding_result[0]:
                        reference_embedding = embedding_result[0]
                        
                        # Find similar products
                        with st.spinner("🔍 Searching for similar products..."):
                            similar_products = find_similar(
                                reference_embedding, 
                                top_k=search_top_k,
                                min_similarity=search_threshold
                            )
                        
                        # Filter out the reference product itself
                        filtered_similar = []
                        for product in similar_products:
                            # Check if this is not the same product (by article number)
                            if product[0] != selected_product[1]:  # article_number comparison
                                filtered_similar.append(product)
                        
                        # Display results
                        if filtered_similar:
                            st.success(f"🎯 Found {len(filtered_similar)} similar product(s)!")
                            
                            # Display similar products
                            for i, (article_number_result, product_name_result, image_path_result, similarity) in enumerate(filtered_similar):
                                with st.expander(f"🏆 Similar Product #{i+1} - {product_name_result or 'N/A'} ({similarity:.1%} similarity)", expanded=(i == 0)):
                                    sim_col1, sim_col2 = st.columns([1, 2])
                                    
                                    with sim_col1:
                                        if image_path_result and os.path.exists(image_path_result):
                                            try:
                                                sim_img = Image.open(image_path_result)
                                                st.image(sim_img, caption="Similar Product", width=150)
                                            except Exception as e:
                                                st.error(f"Error loading image: {e}")
                                        else:
                                            st.write("🖼️ Image not available")
                                    
                                    with sim_col2:
                                        st.write(f"**🏷️ Article Number:** {article_number_result}")
                                        st.write(f"**📦 Product Name:** {product_name_result or 'N/A'}")
                                        st.write(f"**🎯 Similarity Score:** {similarity:.3f}")
                                        st.progress(similarity)
                                        
                                        # Confidence level
                                        if similarity > 0.9:
                                            st.success("🟢 Very High Confidence")
                                        elif similarity > 0.8:
                                            st.success("🟢 High Confidence")
                                        elif similarity > 0.6:
                                            st.warning("🟡 Medium Confidence")
                                        else:
                                            st.info("🔴 Low Confidence")
                        else:
                            st.warning(f"⚠️ No similar products found with similarity >= {search_threshold:.2f}")
                            if search_threshold > 0.0:
                                st.info("💡 Try lowering the similarity threshold to see more results.")
                    else:
                        st.error("❌ No embedding found for the selected product.")
    else:
        st.info("📭 No products with embeddings found in the database. Add some products first!")
        
except Exception as e:
    st.error(f"❌ Error loading products: {e}")

# === Upload New Product Section ===
st.markdown("---")
st.markdown("### 📤 Upload New Product")

# --- OpenAI API Key Section ---
st.markdown("#### 🔑 OpenAI API Key (required for GPT features)")
api_key_input = st.text_input(
    "Enter your OpenAI API key",
    type="password",
    value=st.session_state.get("openai_api_key", ""),
    key="openai_api_key_input"
)
if api_key_input:
    st.session_state["openai_api_key"] = api_key_input

# Add guidance for users to upload packaged product images
st.markdown("#### 📸 Upload Product Image")
st.info("💡 **Tip:** Upload images of products as they appear in their packaging (not opened or loose) for better recognition.")

# Barcode field for future barcode verification support
barcode = st.text_input("🏷️ Enter barcode/EAN (optional, for future verification)", key="barcode")

uploaded_file = st.file_uploader("📤 Upload a product image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="📷 Uploaded Image", use_container_width=True)

    with col2:
        # Encode image with CLIP
        model, preprocess = load_model()
        img_tensor = preprocess(image).unsqueeze(0)
        
        with st.spinner("🔍 Processing image with AI..."):
            with torch.no_grad():
                # Normalize the embedding to improve similarity search accuracy
                embedding = model.encode_image(img_tensor).cpu().numpy().flatten()
                embedding = embedding / np.linalg.norm(embedding)

        # Save uploaded image locally
        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)
        image_filename = f"{uuid.uuid4().hex}.png"
        image_path = os.path.join(upload_folder, image_filename)
        image.save(image_path)

        # Input metadata
        st.markdown("#### 📝 Product Information")
        article_number = st.text_input("🏷️ Article Number (6–32 chars, A-Z, 0-9, '-')", key="article")
        product_name = st.text_input("📦 Product Name", key="product")

        # Action buttons
        col_save, col_check = st.columns(2)
        
        with col_save:
            if st.button("💾 Save to Database", type="primary"):
                article_number = article_number.upper().strip()
                if not article_number or not product_name:
                    st.error("❌ Please enter both article number and product name.")
                elif not re.fullmatch(r"[A-Z0-9-]{6,32}", article_number):
                    st.error("❌ Invalid article number! Must be 6–32 characters: A-Z, 0–9, and hyphen (-) only.")
                else:
                    try:
                        insert_product(article_number, product_name.strip(), image_path, embedding, barcode)
                        st.success(f"✅ Saved {product_name} (Article: {article_number}) to database!")
                    except Exception as e:
                        st.error(f"❌ Error saving to database: {e}")

        with col_check:
            if st.button("🔍 Find Similar Products", type="secondary"):
                if barcode:
                    # Barcode verification
                    product = get_product_by_barcode(barcode)
                    if product:
                        art_num, prod_name, img_path, db_embedding = product
                        if isinstance(db_embedding, list) or isinstance(db_embedding, np.ndarray):
                            db_embedding = np.array(db_embedding, dtype=np.float32)
                        else:
                            db_embedding = np.fromstring(
                                db_embedding.strip("[]"), sep=",", dtype=np.float32
                            )
                        similarity_score = np.dot(embedding, db_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(db_embedding))
                        
                        st.success("🎯 Barcode Verification Result:")
                        col_info, col_img = st.columns([2, 1])
                        with col_info:
                            st.write(f"**Product:** {prod_name}")
                            st.write(f"**Article:** {art_num}")
                            st.write(f"**Similarity:** {similarity_score:.2%}")
                            st.progress(similarity_score)
                        with col_img:
                            if os.path.exists(img_path):
                                st.image(img_path, caption="Database Image", use_container_width=True)
                    else:
                        st.warning("⚠️ No product found with this barcode.")
                else:
                    # Similarity search
                    with st.spinner("🔍 Searching for similar products..."):
                        # Try to get top 3 similar products with very low threshold
                        results = find_similar(embedding, top_k=3, min_similarity=0.0)
                    
                    if results:
                        st.success(f"🎯 Found {len(results)} similar product(s) out of top 3!")
                        
                        # Debug info
                        if len(results) < 3:
                            st.info(f"ℹ️ Only {len(results)} products available in database.")
                        
                        # Display results in a more organized way
                        for idx, (article_number_result, product_name_result, image_path_result, similarity) in enumerate(results):
                            with st.expander(f"🏆 #{idx + 1} Match - {product_name_result} ({similarity:.1%} similarity)", expanded=(idx == 0)):
                                result_col1, result_col2 = st.columns([1, 2])
                                
                                with result_col1:
                                    if image_path_result and os.path.exists(image_path_result):
                                        try:
                                            result_image = Image.open(image_path_result)
                                            st.image(result_image, caption="Product Image", use_container_width=True)
                                        except Exception as e:
                                            st.error(f"Could not load image: {e}")
                                            st.write("🖼️ Image not available")
                                    else:
                                        st.write("🖼️ Image not available")
                                
                                with result_col2:
                                    st.write(f"**📦 Product Name:** {product_name_result}")
                                    st.write(f"**🏷️ Article Number:** {article_number_result}")
                                    st.write(f"**🎯 Similarity Score:** {similarity:.2%}")
                                    st.progress(similarity)
                                    
                                    # Add confidence level
                                    if similarity > 0.8:
                                        st.success("🟢 High Confidence Match")
                                    elif similarity > 0.6:
                                        st.warning("🟡 Medium Confidence Match")
                                    else:
                                        st.info("🔴 Low Confidence Match")
                    else:
                        st.info("ℹ️ No similar products found in the database.")

        # GPT Suggestion
        if st.button("🤖 Suggest Product Info with GPT"):
            openai_api_key = st.session_state.get("openai_api_key")
            if not openai_api_key:
                st.error("❌ OpenAI API key is not set. Please enter your API key above.")
            else:
                with st.spinner("🤖 Generating suggestions with GPT..."):
                    try:
                        suggestion = generate_product_info(
                            f"Photo of {uploaded_file.name}",
                            api_key=openai_api_key
                        )
                        st.info(f"🤖 **GPT Suggestion:**\n{suggestion}")
                    except Exception as e:
                        st.error(f"❌ Error generating product info: {e}")

# IMPROVED: Image Management Section
st.markdown("---")
st.markdown("### 🗂️ Image Management")

upload_folder = "uploads"
uploaded_files_list = get_uploaded_files(upload_folder)

if uploaded_files_list:
    st.write(f"📁 **Total uploaded images:** {len(uploaded_files_list)}")
    
    # Selective removal
    with st.expander("🗑️ Remove Selected Images"):
        selected_files = st.multiselect(
            "Select images to remove:",
            options=uploaded_files_list,
            key="files_to_remove"
        )
        
        if selected_files:
            # Show preview of selected files
            st.write("📋 **Selected files for removal:**")
            preview_cols = st.columns(min(len(selected_files), 4))
            for idx, filename in enumerate(selected_files[:4]):  # Show max 4 previews
                with preview_cols[idx]:
                    file_path = os.path.join(upload_folder, filename)
                    if os.path.exists(file_path):
                        try:
                            img = Image.open(file_path)
                            st.image(img, caption=filename, use_container_width=True)
                        except:
                            st.write(f"📄 {filename}")
            
            if len(selected_files) > 4:
                st.write(f"... and {len(selected_files) - 4} more files")
            
            if st.button("🗑️ Remove Selected Images", type="secondary"):
                try:
                    removed_count = 0
                    for filename in selected_files:
                        file_path = os.path.join(upload_folder, filename)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                st.success(f"✅ Removed: {filename}")
                                removed_count += 1
                            except Exception as e:
                                st.error(f"❌ Could not remove {filename}: {e}")
                    
                    if removed_count > 0:
                        st.success(f"🎉 Successfully removed {removed_count} image(s).")
                        st.rerun()
                    else:
                        st.warning("⚠️ No files were removed.")
                        
                except Exception as e:
                    st.error(f"❌ Error while removing selected images: {e}")
    
    # Remove all images (with confirmation)
    with st.expander("⚠️ Remove ALL Images (Danger Zone)"):
        st.warning("🚨 **Warning:** This will permanently delete ALL uploaded images!")
        confirm_all = st.checkbox("✅ I understand this will delete ALL uploaded images")
        
        if confirm_all and st.button("🗑️ Remove ALL Images", type="secondary"):
            try:
                removed_count = 0
                for root, dirs, files in os.walk(upload_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            removed_count += 1
                        except Exception as e:
                            st.warning(f"Could not remove file {file_path}: {e}")
                
                if removed_count > 0:
                    st.success(f"✅ All {removed_count} uploaded images have been removed successfully.")
                    st.rerun()
                else:
                    st.info("ℹ️ No files found to remove.")
            except Exception as e:
                st.error(f"❌ Error while removing uploaded images: {e}")
else:
    st.info("📁 No uploaded images found.")

# Database Viewer Section
st.markdown("---")
st.markdown("### 📊 Database Viewer & Analytics")

if st.checkbox("🔍 Show Database Contents", key="show_db_contents"):
    try:
        # Database Statistics
        stats = get_database_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Products", stats['total_products'])
        with col2:
            st.metric("With Barcodes", stats['products_with_barcodes'])
        with col3:
            st.metric("Added Today", stats['recent_products'])
        with col4:
            if stats.get('orphaned_records', 0) > 0:
                st.metric("⚠️ Orphaned Records", stats['orphaned_records'], delta="-cleanup needed")
            else:
                st.metric("✅ Database Health", "Clean")
        
        # Show cleanup button if there are orphaned records
        if stats.get('orphaned_records', 0) > 0:
            st.warning(f"Found {stats['orphaned_records']} database records with missing image files.")
            if st.button("🧹 Clean Up Orphaned Records", key="cleanup_db"):
                removed_count = cleanup_orphaned_records()
                st.success(f"Cleaned up {removed_count} orphaned database records!")
                st.rerun()  # Refresh the page to update stats
        
        st.markdown("#### 📋 Active Product Database")
        
        # Fetch all valid products
        products = get_all_products()
        
        if products:
            st.info(f"Showing {len(products)} products with valid image files")
            # Create a more detailed view
            for idx, (id, article_number, product_name, image_path, barcode, created_at, updated_at, embedding_size) in enumerate(products):
                with st.expander(f"🏷️ {product_name} (ID: {id})", expanded=False):
                    prod_col1, prod_col2 = st.columns([1, 2])
                    
                    with prod_col1:
                        # Show product image if available
                        if image_path and os.path.exists(image_path):
                            try:
                                img = Image.open(image_path)
                                st.image(img, caption=f"Product Image", use_container_width=True)
                            except Exception as e:
                                st.write("🖼️ Image not available")
                        else:
                            st.write("🖼️ No image available")
                    
                    with prod_col2:
                        st.write(f"**📦 Product Name:** {product_name}")
                        st.write(f"**🏷️ Article Number:** {article_number}")
                        st.write(f"**📱 Barcode:** {barcode or 'Not set'}")
                        st.write(f"**🧠 Vector Size:** {embedding_size} dimensions")
                        st.write(f"**📅 Created:** {created_at}")
                        st.write(f"**🔄 Updated:** {updated_at}")
                        st.write(f"**📁 Image Path:** `{image_path}`")
        else:
            st.info("No products with valid image files found in database.")
            
    except Exception as e:
        st.error(f"Error loading database contents: {e}")

# Add a comprehensive cleanup section
st.markdown("---")
st.markdown("### 🧹 Database Maintenance")

col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Remove All Uploaded Images", key="remove_images"):
        try:
            upload_folder = "uploads"
            removed_files = 0
            if os.path.exists(upload_folder):
                for root, dirs, files in os.walk(upload_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            removed_files += 1
                        except Exception as e:
                            st.warning(f"Could not remove file {file_path}: {e}")
                st.success(f"Removed {removed_files} uploaded image files.")
            else:
                st.info("No uploads folder found.")
        except Exception as e:
            st.error(f"Error while removing uploaded images: {e}")

with col2:
    if st.button("🗂️ Sync Database with Files", key="sync_db"):
        try:
            removed_count = cleanup_orphaned_records()
            if removed_count > 0:
                st.success(f"Cleaned up {removed_count} orphaned database records!")
            else:
                st.info("Database is already synchronized with image files.")
            st.rerun()  # Refresh to update the display
        except Exception as e:
            st.error(f"Error during database sync: {e}")

st.caption("💡 Tip: Use 'Remove All Uploaded Images' to clear files, then 'Sync Database with Files' to clean up orphaned records.")

# Footer
st.markdown("---")
st.markdown("*🔬 Powered by OpenAI CLIP for advanced image similarity search*")
