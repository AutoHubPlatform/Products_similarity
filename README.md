# maxQ.hyperautomation

# Porducts Recognition powered by OpenAI Search

## Description
This application is designed to assist retail operations by supplementing barcode scanning with advanced image recognition. The goal is to identify products as retail items—specifically as they appear in their packaging—rather than their contents or opened forms. Using the CLIP model, the app encodes product images and compares them to a database to help:

- Recognize products that do not have an EAN/barcode.
- Verify that a scanned product matches its actual image.
- Support efficient product lookup and verification in retail environments.

The app provides a user-friendly interface for uploading packaged product images, storing product metadata, searching for visually similar products, and leveraging AI (via OpenAI GPT, powered by ChatGPT) to suggest a product name after you upload a picture. This foundation enables robust product identification and verification workflows in retail settings.

## Features
- Upload product images and encode them using the CLIP model.
- Save product metadata (article number, product name, and image) to a PostgreSQL database.
- Retrieve and display the top 3 visually similar products from the database.
- User-friendly interface for uploading images and managing product data.

## Explanation of Similarity Score
The similarity score is a numerical value that represents how similar a given product is to another product in the database. For example, a similarity score of `125.745` indicates how closely the uploaded image (e.g., a grape pick) matches the product with article number `123456789`.

### How It Works
- The similarity score is calculated using a machine learning model, such as a neural network, that compares the features of the uploaded image to the features of stored products.
- The score ranges from `0` to a maximum value (e.g., `125` in this case). A higher score indicates a higher degree of similarity between the two products.

### Interpretation
- A high similarity score (e.g., `125.745`) suggests that the uploaded image is very similar to the compared product.
- The score is derived by analyzing various features, such as images, descriptions, or attributes, and identifying patterns and relationships between them.

This similarity score helps users quickly identify products that closely match their uploaded images.

## Installation
### Using Docker Compose
1. Build and start the application:
   ```bash
   docker-compose up --build
   ```
2. Access the app in your browser at `http://localhost:8501`.

### Manual Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Gpt-Shopware
   ```

2. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up the PostgreSQL database:**
   - Create a database named `fruits`.
   - Create the `products` table:
     ```sql
     CREATE TABLE products (
         id SERIAL PRIMARY KEY,
         article_number VARCHAR(32) NOT NULL,
         product_name TEXT NOT NULL,
         image_path TEXT NOT NULL,
         embedding VECTOR(512), -- or FLOAT[] depending on your setup
         barcode VARCHAR(64),
         created_at TIMESTAMP DEFAULT NOW(),
         updated_at TIMESTAMP DEFAULT NOW()
     );
     ```

4. **Configure environment variables:**
   ```bash
   export DB_HOST=your_db_host
   export DB_PORT=your_db_port
   export DB_NAME=fruits
   export DB_USER=your_db_user
   export DB_PASSWORD=your_db_password
   ```

## Usage
1. **Start the Streamlit app:**
   ```bash
   streamlit run app/streamlit_app.py
   ```
2. **Open in your browser:**  
   [http://localhost:8501](http://localhost:8501)
3. **Upload a product image, enter metadata, and save it to the database.**
4. **View the top 3 visually similar products based on the uploaded image.**

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

# 🥝 Product Image Search & GPT Suggestion App

This Streamlit app allows you to:
- Upload product images (preferably in their packaging)
- Store product info and image embeddings in a PostgreSQL database
- Search for similar products using CLIP embeddings
- Optionally, get product info suggestions using OpenAI GPT (with your API key)

---

## 🚀 Features

- **Image Upload:** Upload images of products as they appear in their packaging.
- **Product Database:** Save product name, article number, barcode, and image embedding.
- **Similarity Search:** Find similar products using CLIP model embeddings.
- **Barcode Lookup:** Search by barcode if available.
- **GPT Suggestions:** Get AI-generated product info suggestions (requires OpenAI API key).
- **Image Management:** Remove all uploaded images with one click.

---

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Gpt-Shopware/app
```

### 2. Install Dependencies

It's recommended to use a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

### 3. Configure PostgreSQL

- Make sure you have a PostgreSQL server running.
- Create a database (default: `fruits`).
- Create the `products` table with columns for article number, product name, image path, embedding (vector/array), barcode, created_at, updated_at.

Example table schema:
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article_number VARCHAR(32) NOT NULL,
    product_name TEXT NOT NULL,
    image_path TEXT NOT NULL,
    embedding VECTOR(512), -- or FLOAT[] depending on your setup
    barcode VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

- Adjust the `DB_CONFIG` in `streamlit_app.py` if needed.

### 4. (Optional) Install PostgreSQL Vector Extension

If using the `vector` type for embeddings, install [pgvector](https://github.com/pgvector/pgvector).

---

## 🧑‍💻 Usage

### 1. Start the App

```bash
streamlit run streamlit_app.py
```

### 2. Open in Your Browser

Go to [http://localhost:8501](http://localhost:8501)

### 3. Using GPT Features

- Enter your OpenAI API key in the "OpenAI API Key" field in the app UI (the key should start with `sk-...`).
- The key is only used for your session and not stored permanently.

---

## 📦 File Structure

```
Gpt-Shopware/
  app/
    streamlit_app.py
    gpt_utils.py
    ...
  requirements.txt
  README.md
```

---

## ⚠️ Notes

- Only enter the raw OpenAI API key (not `export ...` or quotes).
- Images are saved in the `uploads/` folder.
- For best results, upload images of products in their original packaging.

---

## 📝 License

MIT License (or your chosen license)

---

## 🙋 Support

For questions or issues, open an issue on the repository or contact the maintainer.