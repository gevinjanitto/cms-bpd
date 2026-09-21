FROM python:3.11-slim
WORKDIR /service
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
RUN useradd --create-home appuser && chown -R appuser:appuser /service
USER appuser
CMD ["python", "run.py"]
