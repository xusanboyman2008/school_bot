libgl1
libgl1-mesa-glx
# Use Python 3.12 slim version as the base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (including libGL.so.1)
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files into the container
COPY . .

# Define the command to run your application
CMD ["python", "main.py"]
