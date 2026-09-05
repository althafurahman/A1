FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir "openpyxl>=3.1,<4" "pandas>=2.2,<3" "numpy>=2.0,<3" "httpx>=0.27,<1"

COPY a1/ a1/

ENV PYTHONUNBUFFERED=1
# Judges: docker run --rm -e OPENROUTER_API_KEY -v <dataset>:/data:ro -v <empty>:/out a1
ENTRYPOINT ["python", "-m", "a1.run", "--dataset-dir", "/data", "--out-dir", "/out"]
