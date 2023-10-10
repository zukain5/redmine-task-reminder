import json
import logging
import os
from datetime import datetime

from redminelib import Redmine
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        overdue_issues = get_overdue_issues()
        logger.info(f'Found {len(overdue_issues)} overdue issues.')
    except Exception:
        get_succeeded = False
        logger.exception('Error occurred while getting overdue issues from Redmine.')
    else:
        get_succeeded = True
        if len(overdue_issues) == 0:
            logger.info('No need to notify slack.')
            return

    try:
        response = notify_slack(overdue_issues, get_succeeded)
        logger.debug(f'Slack API response: {response}')
    except SlackApiError:
        logger.exception('Error occurred while notifying slack.')
        return


def get_overdue_issues():
    redmine_url = os.getenv('REDMINE_URL')
    redmine_api_key = os.getenv('REDMINE_API_KEY')
    redmine = Redmine(redmine_url, key=redmine_api_key)

    today = datetime.today().date()
    overdue_issues = redmine.issue.filter(
        status_id='open',
        due_date=f'<={today}',
        sort='due_date:asc',
    )
    return overdue_issues


def slack_client():
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    return WebClient(token=slack_token)


def notify_slack(overdue_issues, get_succeeded):
    client = slack_client()
    channel_id = os.environ["SLACK_CHANNEL_ID"]

    if get_succeeded:
        response = client.chat_postMessage(
            channel=channel_id,
            text='期限切れのタスクたちをお知らせしますぞ。',
            blocks=build_blocks(overdue_issues),
            unfurl_links=False,
        )
    else:
        response = client.chat_postMessage(
            channel=channel_id,
            text=':warning: 期限切れタスクの通知に失敗しましたぞ。修正してくだされ。 :warning:',
        )

    return response


def notify_slack_error():
    client = slack_client()

    channel_id = os.environ["SLACK_CHANNEL_ID"]
    response = client.chat_postMessage(
        channel=channel_id,
        text=':warning: 期限切れタスクの通知に失敗しましたぞ。修正してくだされ。 :warning:',
    )
    return response


def build_blocks(overdue_issues):
    first_message = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "期限切れのタスクたちをお知らせしますぞ。"
        },
    }

    divider = {
        "type": "divider"
    }

    blocks = [first_message, divider]

    with open('user_mapping.json') as f:
        user_mapping = json.load(f)

    for issue in overdue_issues:
        issue_message = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{issue.url}|#{issue.id} {issue.subject}>*"
            }
        }

        redmine_user_id = issue.assigned_to.id if hasattr(issue, 'assigned_to') else None
        user_slack_id = user_mapping.get(str(redmine_user_id), None)
        assignee = f"<@{user_slack_id}>" if user_slack_id else "なし"
        context_text = f"締切：{issue.due_date}\n担当：{assignee}\nプロジェクト：{issue.project.name}"

        context_message = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": context_text,
                },
            ]
        }

        blocks.append(issue_message)
        blocks.append(context_message)
        blocks.append(divider)

    return blocks
