FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python package
RUN pip install --no-cache-dir -r requirements.txt

# Go work directory
COPY . .

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9007"]