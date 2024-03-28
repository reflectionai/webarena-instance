 To create a new ec2 instance, run the following command and note the public IPv4 address that is returned.
 ```
 aws ec2 run-instances --image-id ami-06290d70feea35450 --count 1 --instance-type t3a.xlarge --key-name webarena --security-group-ids launch-wizard-1 --block-device-mappings DeviceName=/dev/sda1,Ebs={VolumeSize=1250} --user-data file://setup.sh --region us-east-2
 ```
 To ssh into the instance, log into run the following command:
 ```
 ssh -i ~/Downloads/webarena.pem ubuntu@<Public IPv4 address>
 ```
Logs will be stored at `/var/log/cloud-init-output.log`.