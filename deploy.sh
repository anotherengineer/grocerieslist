#!/bin/bash
# Run this on the EC2 instance to pull latest code and restart the app.
set -e

cd /home/ubuntu/grocerieslist
git pull
source .venv/bin/activate
pip install -r requirements.txt -q
sudo systemctl restart groceries
echo "Done. App restarted."
