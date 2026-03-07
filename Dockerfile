FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Just copy the Python script
COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]