import os
import psycopg2
from PIL import Image
from tqdm import tqdm
import torch
import open_clip

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "fruits",
    "user": "postgres",
    "password": "postgres"
}


def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)


def get_image_files(img_dir):
    return [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]


def main():
    img_dir = "fruit_images"
    image_files = get_image_files(img_dir)
    # Example metadata: [(article_number, product_name, filename)]
    metadata = [
        ("A001", "Apple", "apple.jpg"),
        ("A002", "Banana", "banana.jpg"),
        ("A003", "Orange", "orange.jpg"),
        # ...add more as needed...
    ]
    # Load CLIP model
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='openai')
    tokenizer = open_clip.get_tokenizer('ViT-B-32')

    conn = get_db_conn()
    cur = conn.cursor()

    for article_number, product_name, filename in tqdm(metadata):
        img_path = os.path.join(img_dir, filename)
        image = preprocess(Image.open(img_path)).unsqueeze(0)
        with torch.no_grad():
            embedding = model.encode_image(image).cpu().numpy().flatten()
        # Insert into DB
        cur.execute(
            "INSERT INTO products (article_number, product_name, image_path, embedding) VALUES (%s, %s, %s, %s)",
            (article_number, product_name, img_path, embedding.tolist())
        )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
