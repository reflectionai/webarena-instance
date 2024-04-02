 First, ensure that the following environment variables are set:

```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
```

 To create a new ec2 instance, run `bash launch.sh`.
 Wait a few seconds before ssh'ing in (otherwise your connection will be refused). 
To view logs from within the instance, run:
 ```bash
 tail -f /var/log/cloud-init-output.log
 ```
 To check the status of the gitlab database, run
 ```bash
 docker exec -it gitlab tail -f /var/log/gitlab/postgresql/current
 ```