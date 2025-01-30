#!/bin/bash

# Define variables
EXPORTER_DIR="/opt/exim_exporter"
SERVICE_FILE="/etc/systemd/system/exim_exporter.service"
REPO_URL="https://github.com/Alireza-Ramezanzadeh/exim_exporter.git"

# Update system and install dependencies
sudo apt update && sudo apt install -y python3 python3-pip git

# Clone the repository
sudo git clone "$REPO_URL" "$EXPORTER_DIR"
cd "$EXPORTER_DIR"

# Install Python dependencies
sudo pip3 install -r requirements.txt

# Create the systemd service file
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Exim Exporter for Prometheus
After=network.target

[Service]
User=nobody
WorkingDirectory=$EXPORTER_DIR
ExecStart=/usr/bin/python3 $EXPORTER_DIR/exim_exporter.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable exim_exporter
sudo systemctl start exim_exporter

# Check the service status
sudo systemctl status exim_exporter

echo "Exim Exporter installation and service setup complete."
