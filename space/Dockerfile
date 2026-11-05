# Hugging Face Space (Docker SDK) for the payer-policy copilot Streamlit app.
FROM python:3.12-slim

# Spaces run the container as user 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ANONYMIZED_TELEMETRY=False \
    DATA_REPO=ree57/payer-policy-copilot-data
WORKDIR $HOME/app

# CPU-only torch first (the default Linux wheel bundles CUDA and is several GB);
# requirements.txt pins torch==2.15.0, which the +cpu build already satisfies.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.15.0 && \
    pip install --no-cache-dir -r requirements.txt

# Bake the embedding model (~550 MB) into the image so cold starts don't download it.
COPY --chown=user embed.py .
RUN python -c "import embed; embed.load_model(embed.MODEL_NAME)"

COPY --chown=user . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
