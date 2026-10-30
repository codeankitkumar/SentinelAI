# SentinelAI backend container.
# Build context must be the REPO ROOT so the image can also copy the trained ML
# artifacts from ml/models (see docker-compose.yml).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Install backend dependencies first for better layer caching.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Backend application package (importable as `app`).
COPY backend/app ./app

# Trained ML artifacts so inference works out of the box.
COPY ml/models ./ml/models

# The ML sample-dataset generator, so a dataset can be (re)created at runtime.
COPY ml/generate_sample_data.py ./ml/generate_sample_data.py

# Runtime defaults; overridable via compose/.env.
ENV ML_MODEL_PATH=ml/models/sentinel_model.joblib \
    ML_SCALER_PATH=ml/models/scaler.joblib \
    DATABASE_URL=postgresql://sentinel:sentinel_secret@db:5432/sentinelai \
    SEED_DEMO_DATA=true \
    SEED_DEMO_EVENTS=2000 \
    FRONTEND_ORIGIN=http://localhost:5173

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]