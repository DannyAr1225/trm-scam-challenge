FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium

RUN chmod -R a+rX /ms-playwright

RUN useradd \
    --create-home \
    --uid 10001 \
    appuser

COPY . .

RUN mkdir -p /app/output/screenshots \
    && chown -R appuser:appuser /app

USER appuser

CMD [
    "python",
    "-m",
    "agent.main"
]