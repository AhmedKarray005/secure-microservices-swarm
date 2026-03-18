#!/bin/sh
set -eu

LOG_FILE="${LOG_FILE:-/var/log/secure-microservices/api/app.log}"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] monitor: waiting for ${LOG_FILE}"

while [ ! -f "${LOG_FILE}" ]; do
    sleep 2
done

exec tail -n 50 -F "${LOG_FILE}"
