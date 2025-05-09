# Use the official slim Python 3.10 base image
FROM python:3.10-slim

# Set environment variables for Python 3.10 and non-interactive mode
ENV PYTHONUNBUFFERED 1
ENV PATH="/usr/local/bin/python3.10:${PATH}"

# Update and install required dependencies
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libx11-xcb1 \
    build-essential \
    curl \
    wget \
    tesseract-ocr \
    && apt-get clean

# Verify the python version
RUN python3 --version
RUN python3.10 --version

# Set up the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app/

# Copy the requirements.txt and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose the necessary port (optional)
EXPOSE 5000

# Set the environment variable for Chromium to run headless
ENV CHROMIUM_PATH /usr/bin/chromium

# Command to run the application
CMD ["python", "main.py"]
