import logging
import os
from pathlib import Path

import psycopg2
from flask import Flask, jsonify


LOG_DIR = Path(os.getenv("LOG_DIR", "/var/log/secure-microservices/api"))
LOG_FILE = LOG_DIR / "app.log"


def read_secret(secret_value: str | None, secret_file: str | None) -> str | None:
    if secret_value:
        return secret_value

    if secret_file and Path(secret_file).is_file():
        return Path(secret_file).read_text(encoding="utf-8").strip()

    default_secret_file = Path("/run/secrets/db_password")
    if default_secret_file.is_file():
        return default_secret_file.read_text(encoding="utf-8").strip()

    return None


def build_db_config() -> dict:
    return {
        "host": os.getenv("DB_HOST", "db"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "appdb"),
        "user": os.getenv("DB_USER", "appuser"),
        "password": read_secret(
            os.getenv("DB_PASSWORD"),
            os.getenv("DB_PASSWORD_FILE"),
        ),
    }


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    app_logger = logging.getLogger("secure-microservices.api")
    app_logger.info("Logging initialized. Writing API logs to %s", LOG_FILE)
    return app_logger


app = Flask(__name__)
logger = configure_logging()


@app.route("/")
def healthcheck():
    payload = {
        "status": "ok",
        "service": "api",
        "message": "Secure microservices API is healthy.",
    }
    logger.info("Healthcheck requested.")
    return jsonify(payload), 200


@app.route("/db")
def db_check():
    db_config = build_db_config()
    connection = None

    try:
        connection = psycopg2.connect(
            connect_timeout=3,
            **db_config,
        )
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user;")
                database_name, database_user = cursor.fetchone()

        payload = {
            "status": "ok",
            "service": "db",
            "database": database_name,
            "user": database_user,
            "host": db_config["host"],
        }
        logger.info("Database connectivity test succeeded for host=%s.", db_config["host"])
        return jsonify(payload), 200
    except Exception as exc:
        logger.exception("Database connectivity test failed.")
        return (
            jsonify(
                {
                    "status": "error",
                    "service": "db",
                    "message": "Database connectivity failed.",
                    "details": str(exc),
                }
            ),
            503,
        )
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
