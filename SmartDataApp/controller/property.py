#coding:utf-8
import datetime
from decimal import Decimal
import decimal
from django.utils.timezone import utc
from django.http import HttpResponse
import simplejson
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from SmartDataApp.controller.admin import convert_session_id_to_user
from SmartDataApp.controller.complain import push_message
from SmartDataApp.views import index
from SmartDataApp.models import ProfileDetail, Housekeeping, Housekeeping_items,Community,Wallet ,Fee_standard,Property_fee, OrderNumber, Transaction


def add_months(dt, months):
    targetmonth = months + dt.month
    try:
        dt = dt.replace(year=dt.year + int((targetmonth - 1) / 12), month=((targetmonth - 1) % 12) + 1)
    except:
        dt = dt.replace(year=dt.year + int((targetmonth) / 12), month=(((targetmonth ) % 12) + 1), day=1)
        dt += datetime.timedelta(days=-1)
    return dt


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def house_pay_fees(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    btn_style = request.GET.get('btn_style',None)
    communities = Community.objects.all()
    description = "您本年的物业费没交请及时缴纳"
    title = '物业费'
    theme = '亨通物业温馨提示'
    role = '管理员通知'
    if request.user.is_staff:
        now_year = datetime.datetime.now().year
        fee_standard = Fee_standard.objects.filter(type='物业费')
        send_message_status = None
        if fee_standard:
            #判断是否设置截止日期
            if fee_standard[0].deadline != 0 and fee_standard[0].deadline.year != now_year:
                return render_to_response('admin_property_fees_manage.html', { 'btn_style': 2,'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2,'show_warning':True})
            else:
                all_user_info_list = []
                all_user_info = profile.community.profiledetail_set.all()
                for user_info in all_user_info:
                    if user_info.profile.is_staff == False and user_info.is_admin == False:
                        not_pay_fee_num = Property_fee.objects.filter(author=user_info,pay_status=0)
                        not_pay_fee_num = not_pay_fee_num.exclude(deadline__year=now_year)
                        #判断该用户前几年是否已缴费
                        if not not_pay_fee_num:
                            property_fee = Property_fee.objects.filter(author=user_info,deadline__year=now_year)
                            #判断是否是新用户或者今年有没有缴费
                            if property_fee:
                                if property_fee[0].pay_date:#判断是否缴费
                                    pay_status = True
                                else:
                                    if datetime.date.today()>=add_months(property_fee[0].deadline,-1):#如果今天的日期大于等于截止日期那么就发消息通知
                                        if not property_fee[0].send_remind_message:#判断是否已经向该用户发了消息
                                            try:
                                                push_message(description, user_info, title, theme, role)
                                                property_fee[0].send_remind_message = 1
                                            except Exception ,e:
                                                print e
                                    send_message_status = property_fee[0].send_message#催费状态设置
                                    pay_status = False
                            else:
                                property_fee = Property_fee()
                                property_fee.pay_status = 0  #1代表已缴费，默认为0表示未缴费
                                property_fee.author = user_info
                                if fee_standard:
                                    property_fee.deadline = fee_standard[0].deadline
                                property_fee.save()
                                pay_status = False
                            personal_info = {
                                    'personal_profile': user_info.profile,
                                    'phone_number': user_info.phone_number,
                                    'community': user_info.community,
                                    'floor': user_info.floor,
                                    'gate_card': user_info.gate_card,
                                    'address': user_info.address,
                                    'is_admin': user_info.is_admin,
                                    'house_acreage': user_info.house_acreage,
                                    'device_user_id': user_info.device_user_id,
                                    'device_chanel_id': user_info.device_chanel_id,
                                    'device_type': user_info.device_type,
                                    'pay_status': pay_status,
                                    'not_pay_num': None,
                                 }
                            all_user_info_list.append(personal_info)
                        else:
                            not_pay_num = not_pay_fee_num.count()
                            pay_status = False
                            personal_info = {
                                    'personal_profile': user_info.profile,
                                    'phone_number': user_info.phone_number,
                                    'community': user_info.community,
                                    'floor': user_info.floor,
                                    'gate_card': user_info.gate_card,
                                    'address': user_info.address,
                                    'is_admin': user_info.is_admin,
                                    'house_acreage': user_info.house_acreage,
                                    'device_user_id': user_info.device_user_id,
                                    'device_chanel_id': user_info.device_chanel_id,
                                    'device_type': user_info.device_type,
                                    'pay_status': pay_status,
                                    'not_pay_num': not_pay_num,
                                 }
                            all_user_info_list.append(personal_info)
                return render_to_response('admin_property_fees.html', {'user': request.user,'profile': profile,'send_message_status':send_message_status,
                                                               'btn_style': int(btn_style), 'communities': communities,'community': one_community, 'change_community': status,'all_user_info': all_user_info_list})
        else:
            return render_to_response('admin_property_fees_manage.html', { 'btn_style': 2,'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2,'show_warning':True})
    else:
        now_year = datetime.datetime.now().year
        fee_standard = Fee_standard.objects.filter(type='物业费')
        if fee_standard:
            if fee_standard[0].deadline.year != now_year:
                return render_to_response('index.html', {'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2,'show_warning':True})
            else:
                return render_to_response('housing_service_fee.html', {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status})
        else:
            return render_to_response('index.html', {'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2,'show_warning':True})

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def property_fee_manage(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    fee_standard = Fee_standard.objects.filter(type='物业费')
    if fee_standard:
        fee_standard = fee_standard[0]
    else:
        fee_standard = None
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    btn_style = request.GET.get('btn_style',None)
    communities = Community.objects.all()
    if request.user.is_staff:
        return render_to_response('admin_property_fees_manage.html', {'user': request.user,'profile': profile,'fee_standard': fee_standard,
                                                                      'btn_style': int(btn_style), 'communities': communities,'community': one_community, 'change_community': status})

    else:
      return render_to_response('housing_service_fee.html', {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status})



@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def user_pay_property_by_year(request):
    communities = Community.objects.all()
    profile = ProfileDetail.objects.get(profile=request.user)
    person_wallet = Wallet.objects.filter(user_profile=profile)
    if person_wallet:
        person_wallet = person_wallet[0]
    else:
        person_wallet = Wallet()
        person_wallet.user_profile = profile
        person_wallet.save()
    fee_standard = Fee_standard.objects.filter(type='物业费')
    order_num =None
    if fee_standard:
        fee_standard = fee_standard[0]
        total_money = '%.2f'%float(profile.house_acreage*fee_standard.fee*12)
        records = OrderNumber.objects.all()
        record_num = OrderNumber.objects.all().count()
        if not record_num:
            order_number = OrderNumber()
            order_number.number = 10000000
            order_num = 10000000
            order_number.save()
        else:
            order_number = OrderNumber()
            order_number.number = int(records[record_num-1].number)+1
            order_num = int(records[record_num-1].number)+1
            order_number.save()
        property_transaction = Transaction()
        property_transaction.action = '物业缴费'
        property_transaction.time = datetime.datetime.now()
        property_transaction.order_number = str(order_num)
        property_transaction.money_num = decimal.Decimal(str(total_money))
        property_transaction.wallet_profile = person_wallet
        property_transaction.save()
    else:
        fee_standard = None
        total_money = profile.house_acreage*0
    return render_to_response('user_pay_property_by_year.html', {'fee_standard':fee_standard,'user': request.user,'order_num':order_num,
                                                                 'communities': communities, 'profile' : profile, 'change_community': 2, 'total_money': total_money})

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def user_prepare_pay_fee(request):
    communities = Community.objects.all()
    profile = ProfileDetail.objects.get(profile=request.user)

    return render_to_response('user_prepare_pay_fee.html', {'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2})

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def property_user_pay_online(request):
    communities = Community.objects.all()
    profile = ProfileDetail.objects.get(profile=request.user)
    return render_to_response('property_user_pay_online.html',{'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2})


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def property_service(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    if request.user.is_staff:
        return render_to_response('property_service.html', {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status})
    elif profile.is_admin:
       return render_to_response('property_service.html', {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status})
    else:
      return render_to_response('property_service.html', {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status})


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def user_recharge(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    return render_to_response('user_recharge.html',
                                  {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status,})


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def decide_recharge(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    money_num = request.POST.get('money_num', None)
    money_num = Decimal(str(money_num))
    wallet = Wallet.objects.get_or_create(user_profile=profile)[0]
    wallet.money_sum += money_num
    wallet.save()
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    response_data = {'info': '充值成功', 'success': True}
    return HttpResponse(simplejson.dumps(response_data), content_type='application/json')



