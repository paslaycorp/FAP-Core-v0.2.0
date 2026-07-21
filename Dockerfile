FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r fap && useradd -r -g fap fap
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fap_core/ ./fap_core/
COPY api.py .
COPY README.md .
RUN chown -R fap:fap /app
USER fap
EXPOSE 8000
ENV FAP_ENV=production
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
