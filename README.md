# redmine-task-reminder
Redmine task reminder that can run on AWS Lambda.
<!-- TODO: Insert architecture diagram -->

## How to use
1. Create a Redmine API key.
2. Create a Slack Bot And Get the API token.
3. Install the AWS CLI.
4. Install the AWS SAM CLI.
5. Create and configure ./template.yaml and ./function/user_mapping.json
6. run `sam build`
7. run `sam deploy`
8. Lambda function and EventBridge Scheduler are created.

## Configuration
### template.yaml
Below is an example of template.yaml. Customize it to suit your environment.

```yaml
Transform: AWS::Serverless-2016-10-31

Resources:
  Function:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: redmineTaskReminder
      CodeUri: function/
      Handler: function.lambda_handler
      Runtime: python3.11
      Timeout: 3
      Environment:
        Variables:
          REDMINE_URL: https://redmine.example.com
          REDMINE_API_KEY: 1234567890abcdef1234567890abcdef12345678
          SLACK_BOT_TOKEN: xoxb-1234567890-1234567890123-1234567890abcdef1234567890abcdef
          SLACK_CHANNEL_ID: C1234567890
  SchedulerRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Service": "scheduler.amazonaws.com"
              },
              "Action": "sts:AssumeRole"
            }
          ]
        }
      RoleName: redmineTaskReminderSchedulerRole
  SchedulerRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyDocument:
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": [
                "lambda:InvokeFunction"
              ],
              "Effect": "Allow",
              "Resource": "*"
            }
          ]
        }
      PolicyName: redmineTaskReminderSchedulerRolePolicy
      Roles:
        - !Ref SchedulerRole
  Scheduler:
    Type: AWS::Scheduler::Schedule
    Properties:
      FlexibleTimeWindow:
        Mode: "OFF"
      ScheduleExpression: cron(0 13 * * ? *)
      ScheduleExpressionTimezone: Asia/Tokyo
      Target:
        Arn: !GetAtt Function.Arn
        RoleArn: !GetAtt SchedulerRole.Arn
        RetryPolicy:
          MaximumRetryAttempts: 0
```

### function/user_mapping.json
Below is an example of user_mapping.json. It will be used to mention the user in Slack.

```json
{
    // "Redmine user ID": "Slack user ID"
    "1": "U12345678",
    "2": "U23456789",
    "3": "U34567890"
}
```
