FROM python:3.11

# Select working directory
WORKDIR /app

# Copy requirements.txt to working directory
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy required files to working directory
COPY main.py .
COPY config.py .
COPY modules/ ./modules/

# Create data directory + logs and backups directories
RUN mkdir -p /data/{logs,backups}

# Run the bot
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
