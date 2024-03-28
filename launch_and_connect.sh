#!/bin/bash

# Launch the EC2 instance and extract the Instance ID
INSTANCE_JSON=$(aws ec2 run-instances --image-id ami-06290d70feea35450 --count 1 --instance-type t3a.xlarge --key-name webarena --security-group-ids launch-wizard-1 --block-device-mappings DeviceName=/dev/sda1,Ebs={VolumeSize=1250} --user-data file://setup.sh --region us-east-2)
INSTANCE_ID=$(echo "$INSTANCE_JSON" | jq -r '.Instances[0].InstanceId')
echo "Launched EC2 Instance with ID: $INSTANCE_ID"

# Wait for the instance to enter the running state
echo "Waiting for instance to be in 'running' state..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-2
echo "Instance is running."

# Retrieve the Public IPv4 address
export PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[*].Instances[*].PublicIpAddress' --output text --region us-east-2)
echo "Instance Public IP: $PUBLIC_IP"
