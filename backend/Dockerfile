FROM python:3.11-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y gcc g++ libpq-dev libgl1 libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY start_free_tier.sh .
RUN chmod +x start_free_tier.sh

# Use shell script to run both Worker and API (Free Tier Optimization)
CMD ["./start_free_tier.sh"]
