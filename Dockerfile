FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock* requirements.txt* /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir streamlit-pdf-viewer rapidfuzz plotly sqlalchemy

COPY . /app

EXPOSE 8501 8000

CMD ["bash", "-lc", "uvicorn main:fastapi_app --host 0.0.0.0 --port 8000 & streamlit run main.py --server.port 8501 --server.address 0.0.0.0"]
