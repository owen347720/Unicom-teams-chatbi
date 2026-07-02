FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ChromaDB's default embedding function downloads this ONNX model on first use.
# Bake it into the image so offline A100 deployments do not fall back when S3 is unreachable.
RUN python -c "import hashlib, os, tarfile, urllib.request; \
url='https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz'; \
sha='913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3'; \
base='/root/.cache/chroma/onnx_models/all-MiniLM-L6-v2'; \
archive=os.path.join(base, 'onnx.tar.gz'); \
os.makedirs(base, exist_ok=True); \
urllib.request.urlretrieve(url, archive); \
h=hashlib.sha256(open(archive, 'rb').read()).hexdigest(); \
assert h == sha, f'Chroma ONNX model SHA256 mismatch: {h}'; \
tarfile.open(archive, 'r:gz').extractall(base); \
os.remove(archive)"

# Copy application
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /data/chromadb /data/backups /app/logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
