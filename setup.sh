#!/bin/bash
set -x

# Fetch the instance's public hostname
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/public-hostname)

# Start only the Kiwix Docker container which serves Wikipedia content
docker start kiwix33

echo "Kiwix (Wikipedia) container started."

# Optionally, if you need to perform any configurations or checks after starting kiwix33
# For example, verifying that Kiwix is running properly or adjusting configurations based on $HOSTNAME

# Indicate setup completion and log the public hostname for verification
echo "Setup complete. Public hostname: $HOSTNAME"
touch /home/ubuntu/setup_complete.txt
