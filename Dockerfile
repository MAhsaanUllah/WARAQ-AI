FROM python:3.11-slim

WORKDIR /code

# Set cache path so we can pre-download models and use them at runtime
ENV FASTEMBED_CACHE_PATH=/code/.cache
RUN mkdir -p /code/.cache && chmod 777 /code/.cache

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Pre-download AI models during build to save RAM (prevents 512MB OOM on Render)
RUN python -c "from fastembed import TextEmbedding, SparseTextEmbedding; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2'); SparseTextEmbedding(model_name='Qdrant/bm25')"

COPY ./app /code/app
# We don't copy .env directly because secrets are injected by Hugging Face natively!
# But just in case, we can copy it if it exists.
COPY .env* /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
