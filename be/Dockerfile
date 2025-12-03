FROM python:3.11-slim

WORKDIR /app

# HuggingFace Cache
ENV HF_HOME=/app/hf_cache
RUN mkdir -p /app/hf_cache

# ==============================
# System deps
# ==============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    apt-transport-https \
    libzbar0 \
    git \
    libstdc++6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ==============================
# Microsoft repo
# ==============================
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg

RUN echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" \
    > /etc/apt/sources.list.d/msprod.list

RUN apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 \
    mssql-tools18 \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# ==============================
# Python deps
# ==============================
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================
# Pre-download HuggingFace model
# ==============================
RUN python3 - <<EOF
from sentence_transformers import SentenceTransformer
print("Downloading model...")
SentenceTransformer("dangvantuan/vietnamese-embedding")
print("Done.")
EOF

# ==============================
# Copy source code
# ==============================
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
