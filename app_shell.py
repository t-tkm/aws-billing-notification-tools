import os
import json
import boto3
import requests
from datetime import datetime, timedelta, date
from typing import Union

USE_TEAMS_POST="no"
#USE_TEAMS_POST="yes"

if USE_TEAMS_POST == "yes":
#    TEAMS_WEBHOOK_URL =  "https://<YOUR DOMAIN>>.webhook.office.com/webhookb2/XXXXXXXXX"
    TEAMS_WEBHOOK_URL = os.environ['TEAMS_WEBHOOK_URL']

#集計期間自動設定(今月初め〜本日)
def get_date_range() -> Union[str,str]:
    start_date = date.today().replace(day=1).isoformat()
    end_date = date.today().isoformat()
    if start_date == end_date:
        end_of_month = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=-1)
        begin_of_month = end_of_month.replace(day=1)
        return begin_of_month.date().isoformat(), end_date
    return start_date, end_date
(start_date, end_date) = get_date_range()

#集計期間手動設定(不要ならコメントアウト)
(start_date, end_date) = ("2021-11-01", "2021-12-01")

#REST API(get_cost_and_usage)のパラメータ設定
MY_PERIOD={
    'Start': start_date,
    'End': end_date
}

MY_GRANULARITY='MONTHLY'

MY_FILTER={
    'Not': {
        'Dimensions': {
            'Key': "RECORD_TYPE",
            'Values': ["Credit"]
        }
    }
}

MY_METRIC='AmortizedCost'

MY_GROUP_BY= {
    'Type': 'DIMENSION',
    'Key': 'SERVICE'
}

def get_total_cost(inCredit:bool, client) -> str:
    if inCredit:
        response = client.get_cost_and_usage(
            TimePeriod=MY_PERIOD,
            Granularity=MY_GRANULARITY,
            Metrics=[MY_METRIC]
        )
    else:
        response = client.get_cost_and_usage(
            TimePeriod=MY_PERIOD,
            Granularity=MY_GRANULARITY,
            Filter=MY_FILTER,
            Metrics=[MY_METRIC]
        )

    return response['ResultsByTime'][0]['Total'][MY_METRIC]['Amount']
    
def get_service_costs(inCredit:bool, client) -> list:
    if inCredit:
        response = client.get_cost_and_usage(
            TimePeriod=MY_PERIOD,
            Granularity=MY_GRANULARITY,
            Metrics=[MY_METRIC],
            GroupBy=[MY_GROUP_BY]
        )
    else:
        response = client.get_cost_and_usage(
            TimePeriod=MY_PERIOD,
            Granularity=MY_GRANULARITY,
            Filter=MY_FILTER,
            Metrics=[MY_METRIC],
            GroupBy=[MY_GROUP_BY]
        )

    billings = []

    for item in response['ResultsByTime'][0]['Groups']:
        billings.append({
            'service_name': item['Keys'][0],
            'billing': item['Metrics'][MY_METRIC]['Amount']
        })
    return billings

def get_services_msg(service_billings: list) -> dict:
    servicess = []
    for item in service_billings:
        service_name = item['service_name']
        billing = round(float(item['billing']), 2)
        if billing == 0.0: continue
        servicess.append(f'- {service_name}: {billing:.2f}')
    return servicess

def post_teams_webhook(title: str, services: str) -> None:
    payload = {
        "title": title,
        "text": services
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        print(e)
    else:
        print("Teams Webhook Response(Status Code): " + str(response.status_code))

if __name__ == '__main__':
    client = boto3.client('ce', region_name='us-east-1')

    start_day = (datetime.strptime(start_date, '%Y-%m-%d')).strftime('%m/%d')
    end_yesterday = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%m/%d')

    # クレジット適用後費用
    print("------------------------------------------------------")
    total_cost_after_credit = round(float(get_total_cost(True, client)), 2)
    title = f'{start_day} - {end_yesterday}のクレジット適用後費用は{total_cost_after_credit:.2f}(USD)です.'
    print(title)
    services_cost_after_credit = get_services_msg(get_service_costs(True, client))
    print('\n'.join(services_cost_after_credit))
    if USE_TEAMS_POST == "yes":
        post_teams_webhook(title, '\n\n'.join(services_cost_after_credit))

    # クレジット適用前費用
    print("------------------------------------------------------")
    total_cost_before_credit = round(float(get_total_cost(False, client)), 2)
    title = f'{start_day} - {end_yesterday}のクレジット適用前費用は{total_cost_before_credit:.2f}(USD)です.'
    print(title)
    services_cost_before_credit = get_services_msg(get_service_costs(False, client))
    print('\n'.join(services_cost_before_credit))
    print("------------------------------------------------------")
    if USE_TEAMS_POST == "yes":
        post_teams_webhook(title, '\n\n'.join(services_cost_before_credit))