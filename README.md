# maxQ.hyperautomation


# Fruit Similarity Search

## Description
Fruit Similarity Search is a Streamlit-based application that uses AI to find visually similar fruits. By leveraging the CLIP model, the app encodes fruit images into embeddings and compares them to a database of stored fruit images to identify the most similar ones.

## Features
- Upload fruit images and encode them using the CLIP model.
- Save fruit metadata (article number, product name, and image) to a PostgreSQL database.
- Retrieve and display the top 3 visually similar fruits from the database.
- User-friendly interface for uploading images and managing fruit data.

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
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/fruit-similarity-search.git
   ```
2. Navigate to the project directory:
   ```bash
   cd fruit-similarity-search
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the PostgreSQL database:
   - Create a database named `fruits`.
   - Run the SQL script to create the `products` table:
     ```sql
     CREATE TABLE products (
         article_number VARCHAR(32) PRIMARY KEY,
         product_name TEXT NOT NULL,
         image_path TEXT NOT NULL,
         embedding VECTOR(512) NOT NULL,
         created_at TIMESTAMP DEFAULT NOW(),
         updated_at TIMESTAMP DEFAULT NOW()
     );
     ```
5. Configure environment variables for database connection:
   ```bash
   export DB_HOST=your_db_host
   export DB_PORT=your_db_port
   export DB_NAME=fruits
   export DB_USER=your_db_user
   export DB_PASSWORD=your_db_password
   ```

## Usage
1. Start the Streamlit app:
   ```bash
   streamlit run app/streamlit_app.py
   ```
2. Open the app in your browser at `http://localhost:8501`.
3. Upload a fruit image, enter metadata, and save it to the database.
4. View the top 3 visually similar fruits based on the uploaded image.

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.