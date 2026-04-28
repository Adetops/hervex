FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Make our startup script executable
RUN chmod +x run_app.sh

# HF Spaces uses port 7860 by default
EXPOSE 7860

# Run the startup script
CMD ["./run_app.sh"]
