CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    article_number VARCHAR(32) UNIQUE NOT NULL CHECK (article_number ~ '^[A-Z0-9-]{6,32}$'),
    product_name VARCHAR(128) NOT NULL CHECK (product_name <> ''),
    image_path VARCHAR(256) NOT NULL CHECK (image_path ~ '\.(jpeg|jpg|png)$'),
    embedding vector(512) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add barcode column if it does not exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='products' AND column_name='barcode'
    ) THEN
        ALTER TABLE products ADD COLUMN barcode VARCHAR(64);
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_article_number ON products USING HASH (article_number);
CREATE INDEX IF NOT EXISTS idx_product_name_trgm ON products USING GIN (product_name gin_trgm_ops);
