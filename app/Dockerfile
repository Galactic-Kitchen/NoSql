FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --compile -r requirements.txt

COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --compile --no-deps .

RUN addgroup -S app && adduser -S -G app app
USER app

EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--error-logfile=-", "leaderboard.app:app"]