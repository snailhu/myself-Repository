#coding:utf-8
import decimal
import time
import collections
import datetime
from django.contrib.auth.decorators import login_required
from django.db import transaction

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
import requests
from SmartDataApp.models import ChinaPayHistory, OrderNumber,Transaction, Wallet, ProfileDetail,Property_fee,Fee_standard
from SmartDataApp.views import index


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
#@login_required(login_url='/login/')
def quick_pay_conf(request):
    order_num = request.POST.get("order_num",None)
    transaction = Transaction.objects.get(order_number=order_num)
    total_money = transaction.money_num
    service_name = request.POST.get("service_name",None)
    total_money = str(total_money).split('.')[0]+str(total_money).split('.')[1][0:2]
    pay_history = ChinaPayHistory()
    pay_history.order_number = transaction.order_number
    pay_history.user = request.user
    pay_history.save()
    #user = request.user
    #history = ChinaPayHistory.objects.create(user=user)
    #number = OrderNumber.objects.get_or_create(id=1)
    version = '1.0.0'  #消息版本号
    charset = 'UTF-8'  #字符编码
    signMethod = 'MD5'  #签名方法
    # signature = '792c154a3e07aeb13e6d8632cdb14980'  #签名信息
    transType = '01'  #交易类型
    merAbbr = u'用户商城名称'  #商品名称 #todo: use true mer name.
    merId = '105550149170027'  #商品代码
    merCode = ''  #商户类型
    frontEndUrl = "http://192.168.1.113:8001/chinapay/response/front/"
    if service_name == u'property_fee':
        backEndUrl = "http://112.4.82.26:8004/chinapay/property_response/back/"
    acqCode = ''
    orderTime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    orderNumber = ''+str(order_num)+''
    commodityName = str(service_name)
    commodityUrl = ''
    commodityUnitPrice = ''
    commodityQuantity = ''
    transferFee = ''
    commodityDiscount = ''
    orderAmount = total_money
     #todo: change amount here
    orderCurrency = '156'
    customerName = ''
    defaultPayType = ''
    defaultBankNumber = ''
    transTimeout = ''
    customerIp = get_client_ip(request),
    origQid = ''
    merReserved = ''
    secret_key = '88888888'
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
        'commodityName': commodityName,
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
    r = requests.post('https://www.epay.lxdns.com/UpopWeb/api/Pay.action', data=payload, verify=False)
    #r = requests.post('http://www.epay.lxdns.com/UpopWeb/api/BSPay.action ', data=payload, verify=False)
    content = r.text.encode('utf8')
    content = content.replace('/UpopWeb/js/jquery/', '/static/js/')
    return HttpResponse(content)


@csrf_exempt
def pay_response_front(request):
    post_body = request.POST
    #charset = post_body['charset']
    #cupReserved = post_body['cupReserved']
    #exchangeDate = post_body['exchangeDate']
    #exchangeRate = post_body['exchangeRate']
    #merAbbr = post_body['merAbbr']
    #merId = post_body['merId']
    #orderAmount = post_body['orderAmount']
    #orderCurrency = post_body['orderCurrency']
    #qid = post_body['qid']
    #respCode = post_body['respCode']
    #respMsg = post_body['respMsg']
    #respTime = post_body['respTime']
    #settleAmount = post_body['settleAmount']
    #settleCurrency = post_body['settleCurrency']
    #settleDate = post_body['settleDate']
    #signMethod = post_body['signMethod']
    #signature = post_body['signature']
    #traceNumber = post_body['traceNumber']
    #traceTime = post_body['traceTime']
    #transType = post_body['transType']
    #version = post_body['version']
    return redirect(index)

@csrf_exempt
#@transaction.commit_on_success
def pay_response_back(re):
    post_body = re.POST
    charset = post_body['charset']
    cupReserved = post_body['cupReserved']
    exchangeDate = post_body['exchangeDate']
    exchangeRate = post_body['exchangeRate']
    merAbbr = post_body['merAbbr']
    merId = post_body['merId']
    orderAmount = post_body['orderAmount']
    orderNumber = post_body['orderNumber']
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
    pay_history = ChinaPayHistory.objects.get(order_number=orderNumber)
    pay_history.version = version
    pay_history.charset = charset
    pay_history.sign_method = signMethod
    pay_history.signature = signature
    pay_history.trance_type = transType
    pay_history.resp_code = respCode
    pay_history.resp_msg = respMsg
    pay_history.mer_abbr = merAbbr
    pay_history.mer_id = merId
    pay_history.order_number = orderNumber
    pay_history.trance_number = traceNumber
    pay_history.trace_time = traceTime
    pay_history.qid = qid
    pay_history.order_currency = orderCurrency
    pay_history.order_amount = orderAmount
    pay_history.resp_time = respTime
    pay_history.settle_amount = settleAmount
    pay_history.settle_currency = settleCurrency
    pay_history.settle_date = settleDate
    pay_history.exchange_rate = exchangeRate
    pay_history.exchange_date = exchangeDate
    pay_history.cup_reserved = cupReserved
    pay_history.save()
    if respCode == u'00':
        data = {
            'success':True
        }
        return data

    else:
        data = {
            'success': False
            }
        return data

@csrf_exempt
def property_pay_response_back(request):
    data = pay_response_back(re=request)
    if data['success']:
        #money_sum = float(request.POST['orderAmount'][:-2]+'.'+request.POST['orderAmount'][-2:])
        property_history = ChinaPayHistory.objects.get(order_number=request.POST['orderNumber'])
        profile = ProfileDetail.objects.get(profile = property_history.user)
        #person_wallet = Wallet.objects.filter(user_profile=profile)
        #if person_wallet:
        #    person_wallet = person_wallet[0]
        #else:
        #    person_wallet = Wallet.objects.create(user_profile=profile)
        #property_transaction = Transaction()
        #property_transaction.action = '物业缴费'
        #property_transaction.time = datetime.datetime.now()
        #property_transaction.order_number = request.POST['orderNumber']
        #property_transaction.money_num = decimal.Decimal(str(money_sum))
        #property_transaction.wallet_profile = person_wallet
        #property_transaction.save()
        fee_standard = Fee_standard.objects.filter(type='物业费')
        now_year = datetime.datetime.now().year
        not_pay_fee_num = Property_fee.objects.filter(author=profile,pay_status=0)
        if not not_pay_fee_num:
            property_fee = Property_fee.objects.filter(pay_date__year=now_year)
            if property_fee:
                property_fee[0].pay_date = datetime.datetime.now()
                property_fee[0].pay_status = 1  #1代表已缴费，默认为0表示未缴费
                property_fee[0].author = profile
                if fee_standard:
                    property_fee[0].deadline = fee_standard[0].deadline
                property_fee[0].save()
            else:
                property_fee = Property_fee.objects.filter(author=profile,deadline__year=now_year)
                if property_fee:
                    property_fee[0].pay_date = datetime.datetime.now()
                    property_fee[0].pay_status = 1  #1代表已缴费，默认为0表示未缴费
                    property_fee[0].author = profile
                    property_fee[0].save()
                else:
                    property_fee = Property_fee()
                    property_fee.pay_date = datetime.datetime.now()
                    property_fee.pay_status = 1  #1代表已缴费，默认为0表示未缴费
                    property_fee.author = profile
                    if fee_standard:
                        property_fee.deadline = fee_standard[0].deadline
                    property_fee.save()
        else:
            property_fee = not_pay_fee_num[not_pay_fee_num.count()-1]
            property_fee.pay_date = datetime.datetime.now()
            property_fee.pay_status = 1  #1代表已缴费，默认为0表示未缴费
            property_fee.save()
    return HttpResponse('test')
