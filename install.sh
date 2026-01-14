#!/usr/bin/env bash
set -e

echo "Installing Aureli..."

sudo cp aureli /usr/local/bin/aureli
sudo cp au /usr/local/bin/au
sudo chmod +x /usr/local/bin/aureli
sudo chmod +x /usr/local/bin/au

echo "Installation complete."