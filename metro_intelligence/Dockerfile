FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 METRO_DEPLOYMENT=team
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --create-home --uid 10001 metro
COPY --chown=metro:metro app.py analytics.py assistant.py security.py ./
COPY --chown=metro:metro .streamlit/config.toml .streamlit/config.toml
USER metro
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.headless=true"]
