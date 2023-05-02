# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /code

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files to the container
COPY ./app /code/app
COPY .env /code

WORKDIR /code/app

# Expose port 8000 to the host
EXPOSE 8000

# Start the FastAPI app using gunicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]