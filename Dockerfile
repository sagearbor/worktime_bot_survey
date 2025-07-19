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

# Command to run the API using Uvicorn
CMD ["uvicorn", "src.time_profiler.main:app", "--host", "0.0.0.0", "--port", "8000"]
Use a full Python image to build dependencies, which may require system libraries.FROM python:3.11-slim as builderWORKDIR /usr/src/appSet environment variables to prevent Python from writing .pyc filesENV PYTHONDONTWRITEBYTECODE 1ENV PYTHONUNBUFFERED 1Install Poetry for dependency managementRUN pip install poetryCopy only the files needed for dependency installationCOPY pyproject.toml poetry.lock ./Install project dependencies into a virtual environmentRUN poetry config virtualenvs.create false &&   poetry install --no-dev --no-root--- Final Stage ---Use a minimal base image for the final application.FROM python:3.11-slimWORKDIR /usr/src/appCopy the virtual environment from the builder stageCOPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packagesCOPY --from=builder /usr/local/bin /usr/local/binCopy the application source codeCOPY ./src ./srcCOPY ./config ./configExpose the port the app runs onEXPOSE 8000Command to run the application using UvicornThe host 0.0.0.0 is important to expose the server outside the container.CMD ["uvicorn", "src.time_profiler.main:app", "--host", "0.0.0.0", "--port", "8000"]