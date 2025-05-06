FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip gnupg ca-certificates \
    libnss3 libxss1 libappindicator1 libindicator7 \
    fonts-liberation libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 \
    xdg-utils curl && \
    rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN pip install webdriver-manager selenium
RUN pip install -r requirements.txt
# Set display port to avoid errors
ENV DISPLAY=:99
