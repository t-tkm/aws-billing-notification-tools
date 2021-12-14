# aws-billing-notification-tool
## Commands
```
export AWS_PROFILE=<your aws profile>

#コマンドでWebhookを使場合は設定(option)
export TEAMS_WEBHOOK_URL=<your teams webhook URL>

#実行例
% python app_shell.py   
------------------------------------------------------
11/01～11/29のクレジット適用後費用は、205.66 (USD)です。
- AWS Config: 31.21
- AWS Cost Explorer: 2.30
- AWS Secrets Manager: 0.01
- AWS Security Hub: 2.55
- EC2 - Other: 115.99
- Amazon Elastic Compute Cloud - Compute: 17.65
- Amazon Elastic Container Service: 5.90
- Amazon GuardDuty: 0.42
- Amazon Relational Database Service: 8.07
- Amazon Simple Storage Service: 0.61
- AmazonCloudWatch: 1.93
- Tax: 19.02
------------------------------------------------------
11/01～11/29のクレジット適用前費用は、431.12 (USD)です。
- AWS Config: 31.21
- AWS Cost Explorer: 5.25
- AWS Secrets Manager: 0.01
- AWS Security Hub: 3.12
- EC2 - Other: 115.99
- Amazon Elastic Compute Cloud - Compute: 73.81
- Amazon Elastic Container Service: 5.90
- Amazon GuardDuty: 0.42
- Amazon Relational Database Service: 173.03
- Amazon Simple Notification Service: 0.82
- Amazon Simple Storage Service: 0.61
- AmazonCloudWatch: 1.93
- Tax: 19.02
------------------------------------------------------
```
## Deploy Script
AWS SAMを用いたビルド&デプロイスクリプト。

```
#!/bin/sh
set -eu

#aws-root
AWS_PROFILE=root
S3_BACKET=<your backet name>
TEAMS_WEBHOOK_URL=<Teams Webhook URL>

echo "Start sam build command."
sam build

echo "Start sam package command."
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket $S3_BACKET

echo "Start sam deploy command."
sam deploy \
    --template-file packaged.yaml \
    --stack-name NotifyBillingToTeams \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides TeamsWebhookUrl=$TEAMS_WEBHOOK_URL
```

## Delete Stack
```
sam delete --stack-name NotifyBillingToTeams
```