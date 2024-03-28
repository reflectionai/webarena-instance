 To create a new ec2 instance and set the `INSTANCE_ID` and `INSTANCE_PUBLIC_IP` variables, run `source ./launch_and_connect.sh`
 To ssh into the instance, log into run the following command:
 ```bash
 ssh -i ~/Downloads/webarena.pem ubuntu@$PUBLIC_IP
 ```
Logs will be stored at `/var/log/cloud-init-output.log`.