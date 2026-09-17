# Dashboard-maker — a lightweight home server dashboard built with Flask.
#
# Rebuilt from source rather than layered onto a previous tag, so each release
# is a clean image. Base and layer order match the original build, which keeps
# the published layers cache-friendly for anyone pulling an update.
FROM python:3.10-slim

LABEL org.opencontainers.image.title="dashboard-maker" \
      org.opencontainers.image.description="A sleek, lightweight home server dashboard built with Flask. Dynamic UI management, plug-and-play theming, JSON-based storage." \
      org.opencontainers.image.version="1.1.0" \
      org.opencontainers.image.url="https://hub.docker.com/r/randomsi/dashboard-maker" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Dependencies first: this layer is only rebuilt when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Ship the licence with the code, so anyone who pulls the image has the terms.
COPY LICENSE .

EXPOSE 5000

# Report unhealthy if the dashboard stops answering, so `docker ps` and any
# orchestrator can see it. Uses stdlib only — no extra tools in the image.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/').close()"

CMD ["python", "app.py"]
