#coding:utf-8
import decimal
import time
import collections
import sched
import datetime
from django.contrib.auth.decorators import login_required
from SmartDataApp.controller.park import add_months
from SmartDataApp.models import Car_Washing, Park_fee
from django.utils import timezone
from threading import Timer
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
    profile = ProfileDetail.objects.get(profile=request.user)
    order_number=request.POST.get("order_number",None)
    try:
       order=Transaction.objects.get(order_number=order_number)
    except (KeyError,Transaction.DoesNotExist):
        return HttpResponse("pay_error.html")
    else:
        if order.wallet_profile_id!=profile.wallet.id:
            return HttpResponse("pay_error.html")
        else:
#            Timer(5, timer_query_status,(order_number,)).start()
            total_money = order.money_num
            service_name = order.action
            total_money = str(total_money).split('.')[0]+str(total_money).split('.')[1][0:2]
            user = request.user
            history = ChinaPayHistory.objects.create(user=user)
            history.order_number = order_number
            version = '1.0.0'  #消息版本号
            charset = 'UTF-8'  #字符编码
            signMethod = 'MD5'  #签名方法
            # signature = '792c154a3e07aeb13e6d8632cdb14980'  #签名信息
            transType = '01'  #交易类型
            merAbbr = u'商户名称'  #商户名称 #todo: use true mer name.
            merId = '105550149170027'  #商品代码
            merCode = ''  #商户类型
            frontEndUrl = "http://192.168.1.113:8001/chinapay/response/front/"
            if service_name==u"微水洗车":
                backEndUrl="http://112.4.82.26:8004/chinapay/car_washing_pay/back/"
            elif service_name==u"停车费":
                backEndUrl="http://112.4.82.26:8004/chinapay/park_pay_response/back/"
            else:
                backEndUrl = "http://112.4.82.26:8004/chinapay/property_response/back/"
            acqCode = ''
 #           orderTime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())))
            orderTime =order.time.strftime('%Y%m%d%H%M%S')
            orderNumber =order_number
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
        property_history = ChinaPayHistory.objects.get(order_number=request.POST['orderNumber'])
        profile = ProfileDetail.objects.get(profile = property_history.user)
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

@csrf_exempt
def park_pay_response(request):
    data = pay_response_back(re=request)
    if data['success']:
        park_fee = Park_fee.objects.get(order_number=request.POST['orderNumber'])
        property_history = ChinaPayHistory.objects.get(order_number=request.POST['orderNumber'])
        profile = ProfileDetail.objects.get(profile = property_history.user)
        if park_fee.park_type == '买断车位':
            user_park_fee = Park_fee.objects.filter(author=profile,pay_status=1,park_type='买断车位')
            last_park_fee = user_park_fee[user_park_fee.count()-1]
            if park_fee.pay_type == '半年':
                park_fee.deadline = add_months(last_park_fee.deadline,6)
            else:
                park_fee.deadline = add_months(last_park_fee.deadline,12)
            park_fee.pay_status =1
            park_fee.save()



@csrf_exempt
def pay_query(order_number):
    order=Transaction.objects.get(order_number=order_number)
    version = '1.0.0'  #消息版本号
    charset = 'UTF-8'  #字符编码
    signMethod = 'MD5'  #签名方法
    signature = '792c154a3e07aeb13e6d8632cdb14980'  #签名信息
    transType = '01'  #交易类型
    merId = '105550149170027'  #商品代码
    orderTime = order.time.strftime('%Y%m%d%H%M%S')
    secret_key = '88888888'
    payload = {
            'version': version,
            'charset': charset,
            'transType': transType,
            'merId': merId,
            'orderTime': orderTime,
            'orderNumber': order_number,
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
    r = requests.post('https://www.epay.lxdns.com/UpopWeb/api/Query.action', data=payload, verify=False)
    content=r.text.encode("utf-8")
    return HttpResponse(content)

@csrf_exempt
def car_washing_pay_back(request):
    data = pay_response_back(re=request)
    if data['success']:
        car_washing=Car_Washing.objects.get(order_number=request.POST['orderNumber'])
        car_washing.pay_date=timezone.now()
        car_washing.pay_status=1
        return "test"


def timer_query_status(order_number):
    try:
        order = Transaction.objects.get(order_number=order_number)
    except(KeyError , Transaction.DoesNotExist):
        pass
    else:
        if order.action==u'微水洗车':
            car_washing=Car_Washing.objects.get(order_number=order_number)
            status=car_washing.pay_status
            if status==1:
                pass
            else:
                content=pay_query(order_number,)
                if content['success']:
                    car_washing.pay_date=timezone.now()
                    car_washing.pay_status=1
                    return "test"










