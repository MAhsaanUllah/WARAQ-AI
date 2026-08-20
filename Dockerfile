FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# We copy pyproject.toml first to cache the pip install step
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
