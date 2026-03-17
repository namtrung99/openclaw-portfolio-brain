FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY app.py main.py ./
COPY src/ src/
COPY .env.example .env.example

# Streamlit config: disable telemetry, set dark theme
RUN mkdir -p /root/.streamlit
RUN printf '[server]\nheadless = true\nport = 8502\nfileWatcherType = "none"\nenableCORS = false\nenableXsrfProtection = false\n\n[browser]\ngatherUsageStats = false\n' > /root/.streamlit/config.toml

EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py"]
