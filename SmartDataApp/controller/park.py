#coding:utf-8
import datetime
import sys

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import simplejson
from SmartDataApp.controller.property import get_a_order_number

from SmartDataApp.models import ProfileDetail, Park_fee, Community, Fee_standard, Transaction, Wallet


reload(sys)
sys.setdefaultencoding("utf-8")


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def parking_fees(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    all_user_info_list = []
    btn_style = request.GET.get('btn_style',None)
    show_detail_info =None
    if request.user.is_staff:
        all_user_info = profile.community.profiledetail_set.all()
        for user_info in all_user_info:
            if user_info.profile.is_staff == False and user_info.is_admin == False:
                all_user_info_list.append(user_info)
        return render_to_response('admin_park.html',
                                  {'user': request.user, 'profile': profile, 'communities': communities,'btn_style': int(btn_style),
                                   'community': one_community, 'change_community': status,
                                   'all_user_info': all_user_info_list})
    else:
        park_fee = Park_fee.objects.filter(author=profile)
        park_fee = park_fee.exclude(position_num=0)
        if park_fee:
            show_detail_info = True
        else:
            show_detail_info = False
        return render_to_response('park_fees.html',
                                  {'user': request.user, 'profile': profile, 'communities': communities,'show_detail_info':show_detail_info,'park_fee':park_fee,
                                   'community': one_community, 'change_community': status})



@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def user_property_verifyParking(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    park_position_id = request.POST.get('radiobutton', None)
    park_fee = Park_fee.objects.get(id=park_position_id)
    #order_num = None
    #order_num = get_a_order_number(order_num)
    #
    pay_money = None
    total_money = None
    if park_fee.park_type=='买断车位':
        fee_standard = Fee_standard.objects.get(type='买断停车费')
        total_money = fee_standard.fee
        if park_fee.pay_type =='半年':
             pay_money = float(fee_standard.fee/2)
        else:
             pay_money = fee_standard.fee
    if park_fee.park_type == '租停车位':
        fee_standard = Fee_standard.objects.get(type='租赁停车费')
        total_money = fee_standard.fee
        if park_fee.pay_type =='半年':
             pay_money = float(fee_standard.fee/2)
        else:
             pay_money = fee_standard.fee

    #if car_number:
    #    park_fee = Park_fee.objects.filter(author=profile)
    #    if park_fee:
    #        park_fee[0].car_number = car_number
    #        park_fee[0].save()
    #    else:
    #        park_fee = Park_fee(author=profile)
    #        park_fee.car_number = car_number
    #        park_fee.save()
    return render_to_response('user_car_port.html', {
        'user': request.user,
        'profile': profile,
        'communities': communities,
        'community': one_community,
        'change_community': status,
        'park_fee': park_fee,
        'pay_money': pay_money,
        'total_money': total_money
    })


def add_months(dt, months):
    targetmonth = months + dt.month
    try:
        dt = dt.replace(year=dt.year + int((targetmonth - 1) / 12), month=((targetmonth - 1) % 12) + 1)
    except:
        dt = dt.replace(year=dt.year + int((targetmonth) / 12), month=(((targetmonth ) % 12) + 1), day=1)
        dt += datetime.timedelta(days=-1)
    return dt


def get_money(park_fee, park_fee_new, pay_money):
    if park_fee.park_type == '买断车位':
        park_fee_new.park_type = '买断车位'
        park_fee_new.pay_type = '半年'
        fee_standard = Fee_standard.objects.get(type='买断停车费')
        pay_money = '%.2f' % float(fee_standard.fee / 2)
    if park_fee.park_type == '租停车位':
        park_fee_new.park_type = '租停车位'
        park_fee_new.pay_type = '半年'
        fee_standard = Fee_standard.objects.get(type='租赁停车费')
        pay_money = '%.2f' % float(fee_standard.fee / 2)
    return pay_money


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def property_parking_Order(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    park_fee_id = request.POST.get('park_fee_id', None)
    period_parking = request.POST.get('period_parking', None)
    park_fee = Park_fee.objects.get(id=park_fee_id)
    park_fee_new = Park_fee()
    order_num = None
    order_num = get_a_order_number(order_num)
    park_fee_new.order_number = order_num
    park_fee_new.author = profile
    person_wallet = Wallet.objects.filter(user_profile=profile)
    if person_wallet:
        person_wallet = person_wallet[0]
    else:
        person_wallet = Wallet.objects.create(user_profile=profile)
    pay_money = None
    if int(period_parking) == 1:
        if park_fee.park_type == '买断车位':
            park_fee_new.park_type = '买断车位'
            fee_standard = Fee_standard.objects.get(type='买断停车费')
            if park_fee.pay_type == '半年':
                 park_fee_new.pay_type = '半年'
                 pay_money = '%.2f'%float(fee_standard.fee/2)
            else:
                 park_fee_new.pay_type = '一年'
                 pay_money = fee_standard.fee
        if park_fee.park_type == '租停车位':
            park_fee_new.park_type = '租停车位'
            fee_standard = Fee_standard.objects.get(type='租赁停车费')
            if park_fee.pay_type =='半年':
                 park_fee_new.pay_type = '半年'
                 pay_money = '%.2f'%float(fee_standard.fee/2)
            else:
                 park_fee_new.pay_type = '一年'
                 pay_money = fee_standard.fee
    elif int(period_parking) == 6:
        pay_money = get_money(park_fee, park_fee_new, pay_money)
    else:
        if park_fee.park_type == '买断车位':
             park_fee_new.park_type = '买断车位'
             park_fee_new.pay_type = '一年'
             fee_standard = Fee_standard.objects.get(type='买断停车费')
             pay_money = '%.2f'%float(fee_standard.fee)
        if park_fee.park_type == '租停车位':
            park_fee_new.park_type = '租停车位'
            park_fee_new.pay_type = '一年'
            fee_standard = Fee_standard.objects.get(type='租赁停车费')
            pay_money = '%.2f'%float(fee_standard.fee)
    park_fee_new.save()
    deal_transaction = Transaction()
    deal_transaction.action = '停车费'
    deal_transaction.order_number = order_num
    deal_transaction.money_num =pay_money
    deal_transaction.wallet_profile = person_wallet
    deal_transaction.time = datetime.datetime.now()
    deal_transaction.save()
    return render_to_response('park_fee_pay_online.html',
                              {'user': request.user,
                               'profile': profile,
                               'park_fee': park_fee,
                               'pay_money': pay_money,
                               'communities': communities,
                               'order_number': order_num,
                               'period_parking': period_parking,
                               'community': one_community,
                               'change_community': status})



@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def park_fee_manage(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    temporary_fee_standard = Fee_standard.objects.filter(type='租赁停车费')
    permanent_fee_standard = Fee_standard.objects.filter(type='买断停车费')
    if permanent_fee_standard:
        permanent_fee_standard = permanent_fee_standard[0]
    else:
        permanent_fee_standard = None
    if temporary_fee_standard:
        temporary_fee_standard = temporary_fee_standard[0]
    else:
        temporary_fee_standard = None
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    btn_style = request.GET.get('btn_style',None)
    communities = Community.objects.all()
    if request.user.is_staff:
        return render_to_response('admin_park_fee_manage.html', {'user': request.user,'profile': profile,'permanent_fee_standard':permanent_fee_standard,'temporary_fee_standard':temporary_fee_standard,
                                                                      'btn_style': int(btn_style), 'communities': communities,'community': one_community, 'change_community': status})

    else:
      return render_to_response('housing_service_fee.html', {'user': request.user,'profile': profile,'communities': communities,'community': one_community, 'change_community': status})

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def admin_distribute_park_position(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    building_num = request.POST.get('building_num',None)
    position_park = request.POST.get('position_park',None)
    room_num = request.POST.get('room_num',None)
    type_for_parking = request.POST.get('type_for_parking',None)
    pay_for_parking = request.POST.get('pay_for_parking',None)
    community = Community.objects.get(id=community_id)
    user_profile = ProfileDetail.objects.filter(community=community, floor=building_num, gate_card=room_num)
    if user_profile:
        park_position = Park_fee.objects.filter(position_num=int(position_park))
        if park_position:
            response_data = {'success': False, 'info': '该停车位已使用！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:

            park_position = Park_fee()
            park_position.author = user_profile[0]
            if int(type_for_parking) ==1 :
                park_position.park_type = '买断车位'
            if int(type_for_parking) ==2 :
                 park_position.park_type = '租停车位'
            if int(pay_for_parking) ==6 :
                park_position.pay_type = '半年'
            if int(pay_for_parking) ==12 :
                 park_position.pay_type = '一年'
            park_position.position_num = int(position_park)
            park_position.pay_date = datetime.datetime.now()
            park_position.deadline = add_months(park_position.pay_date, int(pay_for_parking))
            park_position.pay_status = 1
            park_position.save()
            response_data = {'success': True, 'info': '增加成功！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

    else:
            response_data = {'success': False, 'info': '没有此用户！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
