# Use the official Python image.
FROM python:3.11-slim

# Create and set working directory
WORKDIR /usr/src/app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install application and dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install .

# Copy application source
COPY src ./src
COPY config ./config

# Expose the port the application will run on
EXPOSE 8000

# Command to run the Flask application
CMD ["python", "src/time_profiler/main.py"]