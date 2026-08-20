FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
# We don't copy .env directly because secrets are injected by Hugging Face natively!
# But just in case, we can copy it if it exists.
COPY .env* /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
