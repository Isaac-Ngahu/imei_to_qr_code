FROM python:3.11-slim

# Install system dependencies required by WeasyPrint
RUN apt-get update && apt-get install -y \
    libgobject-2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libharfbuzz0b \
    libfontconfig1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "app.py"]