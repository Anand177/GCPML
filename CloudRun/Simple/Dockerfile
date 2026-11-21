FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=5052

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5052

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5052} --workers 1 --threads 8 --timeout 120 app:app"]