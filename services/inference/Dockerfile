FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 edgeuser
WORKDIR /app
COPY services/inference/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services/inference/app.py .
COPY product /app/product
RUN mkdir -p /model_store && chown -R edgeuser:edgeuser /app /model_store
USER edgeuser
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8080","--workers","1"]
