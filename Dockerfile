FROM python:3.12-slim

WORKDIR /app
# torch is pulled in by tinker-cookbook; the CPU wheel index keeps the image from dragging in CUDA builds on x86.
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
    "openpyxl>=3.1,<4" "pandas>=2.2,<3" "numpy>=2.0,<3" "httpx>=0.27,<1" \
    "tinker>=0.27.1" "tinker-cookbook>=0.5.7"

# Bake the Qwen3.8 tokenizer so start-up does not depend on Hugging Face being reachable.
RUN python -c "from tinker_cookbook.tokenizer_utils import get_tokenizer; get_tokenizer('Qwen/Qwen3.8-27B')"

COPY a1/ a1/

ENV PYTHONUNBUFFERED=1
# Judges: docker run --rm -e TINKER_API_KEY -e TINKER_PROJECT_ID -v <dataset>:/data:ro -v <empty>:/out a1
# Model is fixed in code (Qwen/Qwen3.8-27B via Tinker).
ENTRYPOINT ["python", "-m", "a1.run", "--backend", "tinker", "--dataset-dir", "/data", "--out-dir", "/out", "--concurrency", "6"]
