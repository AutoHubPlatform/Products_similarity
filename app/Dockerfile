# app/Dockerfile
    FROM python:3.10-bullseye  

WORKDIR /app

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*


# Dependency management
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --retries 10 --timeout 600 \
    --find-links https://download.pytorch.org/whl/torch_stable.html \
    --no-cache-dir -r requirements.txt



# App code
COPY . .

# Port configuration
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

