FROM python:3.11-slim
WORKDIR /app
ARG INSTALL_EXTRAS=false
COPY requirements*.txt ./
RUN if [ "$INSTALL_EXTRAS" = "true" ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    else pip install --no-cache-dir -r requirements-core.txt; fi
COPY rag ./rag
COPY api ./api
COPY streamlit_app.py ./
COPY data ./data
RUN useradd --uid 10001 --create-home appuser \
    && mkdir -p /app/chroma_db && chown -R appuser:appuser /app
USER appuser
EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/health')"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
