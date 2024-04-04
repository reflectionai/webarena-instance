aws ec2 describe-instances \
    --filters "Name=instance.group-id,Values=sg-0ac0947a591b8cfbe" \
    --query "Reservations[].Instances[].PublicDnsName[]" \
    --output json \
    --profile reflection \
    --region us-east-2
