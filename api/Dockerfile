FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    LOG_DIR=/var/log/secure-microservices/api

WORKDIR ${APP_HOME}

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home ${APP_HOME} appuser \
    && mkdir -p ${LOG_DIR} \
    && chown -R appuser:appgroup ${APP_HOME} ${LOG_DIR}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
