FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/be:/app/worker" \
    HF_HOME=/app/hf_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/hf_cache

WORKDIR /app

# -------------------------------------------------------
# Install system dependencies
# -------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    curl \
    gnupg \
    build-essential \
    unixodbc unixodbc-dev \
    libzbar0 \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-vie \
    libtesseract-dev libleptonica-dev \
    git && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------
# Microsoft ODBC Driver repo
# -------------------------------------------------------
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] \
        https://packages.microsoft.com/ubuntu/22.04/prod jammy main" \
        > /etc/apt/sources.list.d/mssql-release.list

# Install ODBC Driver 18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 mssql-tools18 && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# -------------------------------------------------------
# Install Python deps FIRST (very important)
# -------------------------------------------------------
COPY worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------
# Pre-download HuggingFace model AFTER deps installed
# -------------------------------------------------------
RUN mkdir -p /app/hf_cache && \
    python3 - <<EOF
from sentence_transformers import SentenceTransformer
print("Downloading model (pinned revision)...")
SentenceTransformer(
    "dangvantuan/vietnamese-document-embedding",
    revision="6fa4e2f",
    trust_remote_code=True,
    cache_folder="/app/hf_cache"
)
print("Done.")
EOF

# -------------------------------------------------------
# Copy backend + worker
# -------------------------------------------------------
COPY be ./be
COPY worker ./worker

CMD ["python", "-m", "worker.worker"]
