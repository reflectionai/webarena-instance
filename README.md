 # Launching a new instance
 First, ensure that the following environment variables are set:

```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
```
also ensure that you have the secret key `web-arena.pem` in the root of the project.

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

 # Trouble shooting
 ```bash
 ~/webarena-instance aws-credentials ⇡
(webarena-instance-2I4BZPVN-py3.11) nix-shell-env ❯  ssh -i web-arena.pem ubuntu@$PUBLIC_IP 
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for 'web-arena.pem' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "web-arena.pem": bad permissions
ubuntu@3.15.156.217: Permission denied (publickey).
 ```

To remedy this, run: `chmod 600 web-arena.pem`