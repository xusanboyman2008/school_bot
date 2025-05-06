FROM python:3.12-slim

# Install Chromium and Chromedriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libgtk-3-0 \
    wget \
    curl \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables so Selenium can find Chrome/Chromedriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/lib/chromium/chromedriver

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app
WORKDIR /app

# Run your app
CMD ["python", "main.py"]
