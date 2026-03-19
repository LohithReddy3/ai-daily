FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the backend package directory
RUN mkdir backend

# Copy source code into the backend package
COPY . backend/

# Expose port
EXPOSE 8000

# Run FastAPI server
# Running as a module so both relative and absolute imports resolve correctly
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
