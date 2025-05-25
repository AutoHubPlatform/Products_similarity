from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/products/")
async def add_product(
    article_number: str = Form(...),
    product_name: str = Form(...),
    barcode: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    image_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    # Here you would call your DB insert logic
    return {
        "article_number": article_number,
        "product_name": product_name,
        "barcode": barcode,
        "image_path": image_path,
        "status": "Product added (DB logic not shown here)"
    }

@app.get("/products/{article_number}")
async def get_product(article_number: str):
    # Here you would call your DB fetch logic
    return {"article_number": article_number, "status": "Fetched (DB logic not shown here)"}
