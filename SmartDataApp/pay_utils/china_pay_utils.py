#coding:utf-8
import time
import collections
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import requests


def md5(string):
    import hashlib
    import types

    if type(string) is types.StringType:
        m = hashlib.md5()
        m.update(string)
        return m.hexdigest()
    else:
        return ''


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
def mobile_quick_pay_conf(request):
    total_money = request.POST.get("total_money",None)
    version = '1.0.0'  #消息版本号
    charset = 'UTF-8'  #字符编码
    signMethod = 'MD5'  #签名方法
    # signature = '792c154a3e07aeb13e6d8632cdb14980'  #签名信息
    transType = '01'  #交易类型
    merAbbr = u'用户商城名称'  #商品名称
    merId = '105550149170027'  #商品代码
    merCode = ''  #商户类型
    frontEndUrl = "http://192.168.1.113:8001/chinapay/response/front/"
    backEndUrl = "http://192.168.1.113:8001/chinapay/response/back/"
    acqCode = ''
    orderTime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    orderNumber = '0000000009'
    commodityName = ''
    commodityUrl = ''
    commodityUnitPrice = ''
    commodityQuantity = ''
    transferFee = ''
    commodityDiscount = ''
    orderAmount = '100000' #todo: change amount here
    orderCurrency = '156'
    customerName = ''
    defaultPayType = ''
    defaultBankNumber = ''
    transTimeout = ''
    customerIp = get_client_ip(request),
    origQid = ''
    merReserved = ''
    secret_key = '88888888' #todo: use true secret key see doc.
    payload = {
        'version': version,
        'charset': charset,
        'transType': transType,
        'merAbbr': merAbbr,
        'merId': merId,
        'merCode': merCode,
        'frontEndUrl': frontEndUrl,
        'backEndUrl': backEndUrl,
        'acqCode': acqCode,
        'orderTime': orderTime,
        'orderNumber': orderNumber,
        'commodityName': commodityName,
        'commodityUrl': commodityUrl,
        'commodityUnitPrice': commodityUnitPrice,
        'commodityQuantity': commodityQuantity,
        'transferFee': transferFee,
        'commodityDiscount': commodityDiscount,
        'orderAmount': orderAmount,
        'orderCurrency': orderCurrency,
        'customerName': customerName,
        'defaultPayType': defaultPayType,
        'defaultBankNumber': defaultBankNumber,
        'transTimeout': transTimeout,
        'customerIp': customerIp[0],
        'origQid': origQid,
        'merReserved': merReserved
    }
    signature_str = ''
    payload = collections.OrderedDict(sorted(payload.items()))
    for (k, v) in payload.items():
        item = "{}={}&".format(k, v.encode('utf8'))
        signature_str += item
    secret_key_str = md5(secret_key)
    signature_str += secret_key_str
    signature = md5(signature_str)
    payload['signMethod'] = signMethod
    payload['signature'] = signature
    #r = requests.post('https://www.epay.lxdns.com/UpopWeb/api/Pay.action', data=payload, verify=False)
    r = requests.post('http://www.epay.lxdns.com/UpopWeb/api/BSPay.action ', data=payload, verify=False)
    content = r.text.encode('utf8')
    content = content.replace('/UpopWeb/js/jquery/', '/static/js/')
    return HttpResponse(content)


@csrf_exempt
def pay_response_front(request):
    post_body = request.POST
    charset = post_body['charset']
    cupReserved = post_body['cupReserved']
    exchangeDate = post_body['exchangeDate']
    exchangeRate = post_body['exchangeRate']
    merAbbr = post_body['merAbbr']
    merId = post_body['merId']
    orderAmount = post_body['orderAmount']
    orderCurrency = post_body['orderCurrency']
    qid = post_body['qid']
    respCode = post_body['respCode']
    respMsg = post_body['respMsg']
    respTime = post_body['respTime']
    settleAmount = post_body['settleAmount']
    settleCurrency = post_body['settleCurrency']
    settleDate = post_body['settleDate']
    signMethod = post_body['signMethod']
    signature = post_body['signature']
    traceNumber = post_body['traceNumber']
    traceTime = post_body['traceTime']
    transType = post_body['transType']
    version = post_body['version']
    return HttpResponse('test')

@csrf_exempt
def pay_response_back(request):
    post_body = request.POST
    charset = post_body['charset']
    cupReserved = post_body['cupReserved']
    exchangeDate = post_body['exchangeDate']
    exchangeRate = post_body['exchangeRate']
    merAbbr = post_body['merAbbr']
    merId = post_body['merId']
    orderAmount = post_body['orderAmount']
    orderCurrency = post_body['orderCurrency']
    qid = post_body['qid']
    respCode = post_body['respCode']
    respMsg = post_body['respMsg']
    respTime = post_body['respTime']
    settleAmount = post_body['settleAmount']
    settleCurrency = post_body['settleCurrency']
    settleDate = post_body['settleDate']
    signMethod = post_body['signMethod']
    signature = post_body['signature']
    traceNumber = post_body['traceNumber']
    traceTime = post_body['traceTime']
    transType = post_body['transType']
    version = post_body['version']
    return HttpResponse('test')

