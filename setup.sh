#!/bin/bash
docker start gitlab
docker start shopping
docker start shopping_admin
docker start forum
docker start kiwix33
cd /home/ubuntu/openstreetmap-website/
docker compose start
sleep 60 # Wait for services to start
# Replace <your-server-hostname> with the actual hostname obtained dynamically
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/public-hostname)
sed -i "s|<your-server-hostname>|${HOSTNAME}|g" setup_host.sh
