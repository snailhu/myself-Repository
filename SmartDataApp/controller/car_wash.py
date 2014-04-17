#coding:utf-8

import threading
import time
import datetime
import json
from urllib import unquote
from django.http import HttpResponse, HttpRequest
import simplejson
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
#from SmartDataApp.controller.admin import convert_session_id_to_user
from SmartDataApp.controller.admin import convert_session_id_to_user
from SmartDataApp.models import Complaints, Repair
from SmartDataApp.pusher.Channel import Channel
from SmartDataApp.views import index
from SmartDataApp.models import ProfileDetail, Community,Wallet
from SmartDataApp.models import Car_Washing
import hashlib
import re

@csrf_exempt
@login_required(login_url='/login/')
def local_life(request):
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
        return render_to_response('admin_car_washing.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'profile': profile,
            'is_admin': False,
            'btn_style': 'once'

        })
    else:
        return render_to_response('user_micro_water.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'profile': profile,
            'is_admin': False,
            'btn_style': 'once'
        })



@csrf_exempt
@login_required(login_url='/login/')
def car_washing(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    page = request.GET.get('page')
    deal_status = request.GET.get("status", None)
    if deal_status=="once":
        washing_info=Car_Washing.objects.all().filter(washing_type="1")
    elif deal_status=="month":
        washing_info=Car_Washing.objects.all().filter(washing_type="2")
    elif deal_status=="season":
        washing_info=Car_Washing.objects.all().filter(washing_type="3")
    else:
        washing_info=Car_Washing.objects.all().filter(washing_type="4")
    paginator = Paginator(washing_info, 5)

    try:
        car_washing_info = paginator.page(page)
    except PageNotAnInteger:
        car_washing_info = paginator.page(1)
    except EmptyPage:
        car_washing_info = paginator.page(paginator.num_pages)
    if request.user.is_staff:
        return render_to_response('admin_car_washing.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'profile': profile,
            'is_admin': False,
            'btn_style':deal_status,
            "car_washing_info":car_washing_info
        })


@csrf_exempt
@login_required(login_url='/login/')
def micro_water_detail(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        profile = ProfileDetail.objects.get(profile=request.user)
        washing_type = request.POST.get(u'washing-type', None)
        single_time=request.POST.get(u'single-time', None)
        month_time=request.POST.get(u'month-time', None)
        car_num=request.POST.get(u'car-num', None)
        washing_case=request.POST.get(u'washing-case', None)
        pattern=re.compile(ur'^[苏,京,粤,津,沪,渝,冀,豫,云,辽,黑,湘,皖,鲁,新,浙,赣,鄂,桂,甘,晋,蒙,陕,吉,闽,贵,青,藏,川,宁,琼,港,澳]{1}[A-Z]{1}[0-9_A-Z]{5}$')
        if not car_num:
            response_data = {'car_num_error': True, 'error_message': u'车牌号不能为空', 'user': request.user, 'profile':profile}
            return render_to_response('user_micro_water.html',response_data)
        if not pattern.match(car_num):
            response_data = {'car_num_error': True, 'error_message': u'车牌号不正确', 'user': request.user, 'profile': profile}
            return render_to_response('user_micro_water.html',response_data)
        washing = Car_Washing()
        if washing_type == u'1':
            if not single_time:
                response_data = {'single_time_error': True, 'error_message': u'请选择开始时间', 'user': request.user, 'profile': profile}
                return render_to_response('user_micro_water.html',response_data)
            washing.washing_type = washing_type
            washing.start_time=single_time
            washing.author=profile
            washing.other_car_num=car_num
            washing.save()
            return render_to_response('user_micro_water_detail.html', {
                "user":profile.profile,
                'profile':profile,
                "washing_type": washing_type,
                "washing_case":washing_case,
                "start_time": single_time,
                "car_num": car_num,
                "single_status": True
            })
        else:
            if not month_time:
                response_data = {'month_time_error': True, 'error_message': u'请选择开始时间', 'user': request.user}
                return render_to_response('user_micro_water.html',response_data)
            washing.start_time=month_time
            washing.author=profile
            washing.washing_type=washing_type
            washing.washing_case=washing_case
            washing.other_car_num=car_num
            washing.save()
        return render_to_response('user_micro_water_detail.html', {
            "user":profile.profile,
            'profile': profile,
            "washing_type": washing_type,
            "start_time": month_time,
            "washing_case": washing_case,
            "car_num": car_num,
            "month_status": True
        })

@transaction.atomic
@csrf_exempt
def micro_water_add(request):
    response_data = {'info': u'添加成功', 'success': True}
    return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def own_car_washing(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    wallet = Wallet.objects.filter(user_profile=profile)
    if wallet:
        wallet = wallet[0]
    car_washing_list=Car_Washing.objects.filter(author=profile)
    paginator = Paginator(car_washing_list, 5)
    page = request.GET.get('page')
    try:
        car_washing_info = paginator.page(page)
    except PageNotAnInteger:
        car_washing_info = paginator.page(1)
    except EmptyPage:
        car_washing_info = paginator.page(paginator.num_pages)
    return render_to_response("own_car_washing.html", {
               'car_washing_info': car_washing_info,
               'user': request.user,
               'wallet': wallet,
               'profile': profile,
               })

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def own_car_washing_detail(request):
    id = request.GET.get("id",None)
    profile = ProfileDetail.objects.get(profile=request.user)
    try:
        detail=Car_Washing.objects.filter(pk=id)
    except(KeyError, Car_Washing.DoesNotExist):
        return render_to_response("own_car_washing.html")
    else:
        return render_to_response("own_car_washing_detail.html",{'detail': detail.get(),'profile': profile})

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def own_car_washing_delete(request):
    id_array=request.POST.get("id",None)
    if id_array:
        list_id=str(id_array).split(",")
        for i in range(len(list_id)):
            id = int(list_id[i])
            del_data=Car_Washing.objects.filter(id=id)
            del_data.delete()
    response_data = {'info': u'删除成功', 'success': True}
    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

def car_washing_detail(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    id=request.GET.get("id",None)
    status=request.GET.get("status",None)
    detail=Car_Washing.objects.filter(pk=id)
    return render_to_response("admin_car_washing_detail.html",{
                                  'detail': detail.get(),
                                  'status':status,
                                  'user':request.user,
                                  'profile': profile,
    })





