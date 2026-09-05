FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir "openpyxl>=3.1,<4" "pandas>=2.2,<3" "numpy>=2.0,<3" "httpx>=0.27,<1" \
    "tinker>=0.27.1" "tinker-cookbook>=0.5.7"

COPY a1/ a1/

ENV PYTHONUNBUFFERED=1
# Judges: docker run --rm --env-file .env -v <dataset>:/data:ro -v <empty>:/out a1
# Needs TINKER_API_KEY and TINKER_PROJECT_ID (see .env.example). Model is fixed in code.
ENTRYPOINT ["python", "-m", "a1.run", "--backend", "tinker", "--dataset-dir", "/data", "--out-dir", "/out", "--concurrency", "6"]
