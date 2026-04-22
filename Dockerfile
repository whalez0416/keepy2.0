# Use the official Playwright image for Python
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies
# The base image already has them, but this ensures they are ready for the app user.
RUN playwright install chromium --with-deps

# Copy the rest of the application
COPY . .

# Create a directory for persistent data (SQLite, Screenshots)
RUN mkdir -p /data/screenshots && chmod -R 777 /data

# Set environment variables
ENV DATABASE_URL=sqlite:////data/keepy.db
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port (Railway will provide this via PORT env var)
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
