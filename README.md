 ```
 aws ec2 run-instances --image-id ami-06290d70feea35450 --count 1 --instance-type t3a.xlarge --key-name webarena --security-group-ids launch-wizard-1 --block-device-mappings DeviceName=/dev/sda1,Ebs={VolumeSize=1250} --user-data file://setup.sh --region us-east-2
 ```