#!/usr/bin/env bash

# Exit if any command fails
set -e

echo "Updating system and installing dependencies..."
sudo apt-get update && sudo apt-get install -y unzip wget curl

echo "Installing Google Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt-get -fy install

echo "Installing Chromedriver..."
CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}' | cut -d '.' -f 1)
wget -q "https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver

echo "Setup complete!"
