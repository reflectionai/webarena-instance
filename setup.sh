#!/bin/bash
set -x

start_time=$(date +%s)

# Start Docker containers
docker start gitlab
docker start shopping
docker start shopping_admin
docker start forum
docker start kiwix33
cd /home/ubuntu/openstreetmap-website/
docker compose start

# Fetch the instance's public hostname
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/public-hostname)

# Wait for services to start
# Dockerize and run the Flask application
cd /home/ubuntu/webarena/environment_docker/webarena-homepage
perl -pi -e "s|<your-server-hostname>|http://${HOSTNAME}|g" /home/ubuntu/webarena/environment_docker/webarena-homepage/templates/index.html
perl -pi -e "s|http://metis.lti.cs.cmu.edu:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing|http://${HOSTNAME}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing|g" templates/index.html

curl -o Dockerfile https://raw.githubusercontent.com/reflectionai/webarena-instance/main/Dockerfile
docker build -t webarena-homepage .
docker run -d -p 4399:4399 webarena-homepage
echo "Webarena homepage is running on port 4399"

sleep 60

# Magento setup with dynamic hostname
docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${HOSTNAME}:7770" # no trailing /
docker exec shopping mysql -u magentouser -pMyPassword magentodb -e "UPDATE core_config_data SET value='http://${HOSTNAME}:7770/' WHERE path = 'web/secure/base_url';"

# Remove the requirement to reset password
docker exec shopping_admin php /var/www/magento2/bin/magento config:set admin/security/password_is_forced 0
docker exec shopping_admin php /var/www/magento2/bin/magento config:set admin/security/password_lifetime 0
docker exec shopping /var/www/magento2/bin/magento cache:flush

# Additional Magento admin setup with dynamic hostname
docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://${HOSTNAME}:7780"
docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e "UPDATE core_config_data SET value='http://${HOSTNAME}:7780/' WHERE path = 'web/secure/base_url';"
docker exec shopping_admin /var/www/magento2/bin/magento cache:flush

CONTAINER_NAME="gitlab"

wait_start_time=$(date +%s)

# Loop until the container's health status is "healthy"
while true; do
    # Get the current health status of the container
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME")
    echo "$CONTAINER_NAME is $HEALTH_STATUS."

    # Check if the health status is "healthy"
    if [ "$HEALTH_STATUS" == "healthy" ]; then
        break
    fi

    # Calculate and echo the wait duration each loop iteration
    wait_time=$(date +%s)
    wait_duration=$((wait_time-wait_start_time))
    echo "Waited $wait_duration seconds for $CONTAINER_NAME to become healthy."
    sleep 10
done

# GitLab configuration update with dynamic hostname
docker exec gitlab sed -i "s|^external_url.*|external_url 'http://${HOSTNAME}:8023'|" /etc/gitlab/gitlab.rb
docker exec gitlab gitlab-ctl reconfigure

end_time=$(date +%s)
total_time=$((end_time-wait_start_time))
touch /home/ubuntu/setup_complete.txt
echo "Setup complete. Total duration: $total_time seconds."