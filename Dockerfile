FROM python:3.12-slim-trixie
ARG POSTGRES_MAJOR=17
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/sngsc
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && mkdir -p /usr/share/postgresql-common/pgdg \
    && curl --fail --silent --show-error https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc
COPY deploy/pgdg.sources /etc/apt/sources.list.d/pgdg.sources
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client-${POSTGRES_MAJOR} \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip check && python -c "import greenlet, argon2, cryptography, fastapi, openpyxl, pydantic, pydantic_settings, reportlab, psycopg, jinja2, uvicorn; from sqlalchemy.ext.asyncio import create_async_engine"
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN useradd --create-home --uid 10001 sngsc \
    && mkdir -p uploads/private uploads/documents uploads/rapports uploads/temporaires app/uploads/avatars logs backups \
    && mkdir -p /var/www && ln -s /srv/sngsc /var/www/api_hauqe \
    && chown -R sngsc:sngsc /srv/sngsc
USER sngsc
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
