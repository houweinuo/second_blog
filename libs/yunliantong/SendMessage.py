from random import randint

from ronglian_sms_sdk import SmsSDK

accId = '8a216da87b3e7006017b4da08f5402c0'
accToken = '565cf766513a48e4b154a2fb55d89d0f'
appId = '8a216da87b3e7006017b4da0906202c6'


def send_message(tid, mobile, datas):
    sdk = SmsSDK(accId, accToken, appId)
    sdk.sendMessage(tid, mobile, datas)

