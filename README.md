 To create a new ec2 instance, run `bash launch.sh`.
 Wait a few seconds before sshing in (otherwise your connection will be refused). 
To view logs from within the instance, run:
 ```bash
 tail -f /var/log/cloud-init-output.log
 ```
 To check the status of the gitlab database, run
 ```bash
 docker exec -it gitlab tail -f /var/log/gitlab/postgresql/current
 ```