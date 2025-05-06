# Use Python 3.12 slim version as the base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (including Chromium and libraries for OpenCV and Selenium)
RUN apt-get update && \
    apt-get install -y \
    chromium \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container
COPY . .

# Set environment variables to specify Chromium path
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

# Run the application
CMD ["python", "main.py"]
