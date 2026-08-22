FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Pre-download AI models during build to save RAM (prevents 512MB OOM on Render)
RUN python -c "from fastembed import TextEmbedding, SparseTextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5'); SparseTextEmbedding(model_name='Qdrant/bm25')"

COPY ./app /code/app
# We don't copy .env directly because secrets are injected by Hugging Face natively!
# But just in case, we can copy it if it exists.
COPY .env* /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
