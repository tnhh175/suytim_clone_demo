FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --user-group --uid 10001 demo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY web/forms.html web/forms.css web/forms.js web/
COPY scripts/run_hosted_forms.py scripts/bootstrap_hosted_forms.py scripts/seed_form_demo.py scripts/
COPY database/schema.sql database/schema.sql
COPY database/migrations/ database/migrations/
USER demo
CMD ["python", "scripts/run_hosted_forms.py"]
