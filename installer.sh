#!/bin/bash

# Define variables
EXPORTER_DIR="/opt/exim_exporter"
SERVICE_FILE="/etc/systemd/system/exim_exporter.service"
REPO_URL="https://github.com/Alireza-Ramezanzadeh/exim_exporter.git"

# Check the operating system
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$ID
else
    echo "Unable to determine OS."
    exit 1
fi

# Install dependencies based on the OS
if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ]; then
    sudo apt update && sudo apt install -y python3 python3-pip git
elif [ "$OS" == "almalinux" ] || [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
    sudo dnf update -y && sudo dnf install -y python3 python3-pip git
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Check if exporter directory already exists
if [ -d "$EXPORTER_DIR" ]; then
    echo "Exim Exporter is already installed. Pulling the latest changes."
    cd "$EXPORTER_DIR"
    sudo git pull origin main
else
    # Clone the repository if not already installed
    echo "Cloning Exim Exporter repository."
    sudo git clone "$REPO_URL" "$EXPORTER_DIR"
    cd "$EXPORTER_DIR"
fi

# Install Python dependencies
echo "Installing Python dependencies."
sudo pip3 install -r requirements.txt

# Create or update the systemd service file
echo "Creating/updating the systemd service file."
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Exim Exporter for Prometheus
After=network.target

[Service]
WorkingDirectory=$EXPORTER_DIR
ExecStart=/usr/bin/python3 $EXPORTER_DIR/exim_exporter.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd, enable and start the service
echo "Reloading systemd and starting Exim Exporter service."
sudo systemctl daemon-reload
sudo systemctl enable exim_exporter
sudo systemctl restart exim_exporter

# Check the service status
sudo systemctl status exim_exporter

echo "Exim Exporter installation and service setup complete."
