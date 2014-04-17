#coding:utf-8
import hashlib
import re
import threading

from captcha.models import CaptchaStore
import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
import simplejson
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User


from SmartDataApp.models import ProfileDetail, Community, Complaints, Repair, Express, Fee_standard,Property_fee
from SmartDataApp.pusher import Channel
from SmartDataApp.views import index, random_captcha

apiKey = "xS8MeH5f4vfgTukMcB2Bo6Ea"
secretKey = "chcxUOTIvBkItk91bXbXxQw5VSAaYhBb"

def push_message(description, handler_detail, title, theme, role):
    c = Channel(apiKey, secretKey)
    push_type = 1
    optional = dict()
    optional[Channel.USER_ID] = int(handler_detail.device_user_id)
    optional[Channel.CHANNEL_ID] = int(handler_detail.device_chanel_id)
    #推送通知类型
    optional[Channel.DEVICE_TYPE] = 4
    if handler_detail.device_type == 'android':
        optional[Channel.MESSAGE_TYPE] = 0
    else:
        optional[Channel.MESSAGE_TYPE] = 1
    optional['phone_type'] = str(handler_detail.device_type)
    message_key = hashlib.md5(str(datetime.datetime.now())).hexdigest()
    message = "{'title': '" + title + "','description': '" + description + "','theme': '" + theme + "','role': '" + role + "'}"
    c.pushMessage(push_type, message, message_key, optional)



class ThreadClass(threading.Thread):
  def __init__(self, description, handler_detail, title, theme, role):
      threading.Thread.__init__(self)
      self._description = description
      self._handler_detail = handler_detail
      self._title = title
      self._theme = theme
      self._role = role
  def run(self):
    #push_message(self._description, self._handler_detail, self._title)
    try:
        push_message(self._description, self._handler_detail, self._title, self._theme, self._role)
    except Exception ,e:
        print e
        push_message(self._description, self._handler_detail, self._title, self._theme, self._role)



def validateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


@transaction.atomic
@csrf_exempt
@login_required
def register(request):
    if request.method != 'POST':
        communities = Community.objects.all()
        profile = ProfileDetail.objects.get(profile=request.user)
        response_data = {
            'success': True,
            'profile': profile,
            'user': request.user,
            'communities': communities
        }
        response_data.update(csrf(request))
        return render_to_response('register.html', response_data)
    else:
        communities = Community.objects.all()
        username = request.POST.get(u'username', None)
        password = request.POST.get(u'password', None)
        repeatPwd = request.POST.get(u'repeatPwd', None)
        mobile = request.POST.get(u'mobile', None)
        email = request.POST.get(u'email', None)
        community_id = request.POST.get(u'community', None)
        is_admin = request.POST.get(u'is_admin', None)
        floor = request.POST.get(u'floor', None)
        gate_card = request.POST.get(u'gate_card', None)
        address = request.POST.get(u'address', None)
        house_acreage = request.POST.get(u'house_acreage', None)
        if len(User.objects.filter(username=username)) > 0:
            response_data = {'username_error': True, 'info': u'用户名已存在', 'user': request.user,
                             'communities': communities}
            return render_to_response('register.html', response_data)
        if password != repeatPwd:
            response_data = {'password_error': True, 'info': u'两次密码输入不相同', 'user': request.user,
                             'communities': communities}
            return render_to_response('register.html', response_data)
        pattern = re.compile(r'^[a-zA-Z0-9]{6,15}$')
        if not pattern.match(password):
            response_data = {'password_error': True, 'info': u'密码：字母、数字组成，6-15位', 'user': request.user,
                             'communities': communities}
            return render_to_response('register.html', response_data)
        pattern = re.compile(r'^(1[0-9][0-9])\d{8}$')
        if not pattern.match(mobile):
            response_data = {'mobile_error': True, 'info': u'请输入正确的手机号码', 'user': request.user,
                             'communities': communities}
            return render_to_response('register.html', response_data)
        pattern = re.compile(r'^\d+(\.\d*)?|\.\d+$')
        if not pattern.match(house_acreage):
            response_data = {'acreage_error': True, 'info': u'**请输入数字**', 'user': request.user,
                             'communities': communities}
            return render_to_response('register.html', response_data)
        if not validateEmail(email):
            response_data = {'email_error': True, 'info': u'请输入正确的邮箱地址', 'user': request.user,
                             'communities': communities}
            return render_to_response('register.html', response_data)
        user = User(username=username)
        user.email = email
        user.password = make_password(password, 'md5')
        if is_admin == u'2':
            user.is_staff = True
        user.save()
        profile_detail = ProfileDetail(profile=user)
        profile_detail.phone_number = mobile
        community = Community.objects.get(id=community_id)
        profile_detail.community = community
        profile_detail.floor = floor
        profile_detail.gate_card = gate_card
        profile_detail.address = address
        profile_detail.is_admin = True if is_admin == u'1' else False
        profile_detail.house_acreage = house_acreage
        profile_detail.save()
        return redirect(index)


@csrf_exempt
def login(request):
    if request.method != u'POST':
        communities = Community.objects.all()
        response_data = random_captcha()
        response_data['communities'] = communities
        return render_to_response('login.html', response_data)
    else:
        captcha_list = CaptchaStore.objects.filter(hashkey=request.POST.get(u'cptch_key', None))
        communities = Community.objects.all()
        if len(captcha_list) == 0:
            response_data = random_captcha()
            response_data['communities'] = communities
            response_data['captcha_info'] = u'验证码不正确.'
            return HttpResponse(simplejson.dumps({'success': False, 'info': '验证码错误'}), content_type='application/json')
        result = captcha_list[0].response
        verify_code = request.POST.get(u'verify_code', None)
        if result != verify_code:
            response_data = random_captcha()
            response_data['communities'] = communities
            response_data['captcha_info'] = u'验证码不正确.'
            return HttpResponse(simplejson.dumps({'success': False, 'info': '验证码错误'}), content_type='application/json')
        username = request.POST.get(u'username', None)
        password = request.POST.get(u'password', None)
        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                auth_login(request, user)
                if not request.POST.get(u'remember_me', None):
                  request.session.set_expiry(0)
                return HttpResponse(simplejson.dumps({'success': True}), content_type='application/json')
            else:
                response_data = random_captcha()
                response_data['communities'] = communities
                response_data['password_info'] = u'手机号码、账号或密码错误.'
                return HttpResponse(simplejson.dumps({'success': False, 'info': '手机号码、账号或密码错误'}), content_type='application/json')


def logout(request):
    auth_logout(request)
    return redirect(index)


def return_error_response():
    response_data = {'error': 'Just support POST method.'}
    return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


def return_404_response():
    return HttpResponse('', content_type='application/json', status=404)


def convert_session_id_to_user(request):
    try:
        session = Session.objects.get(session_key=request.META['HTTP_SESSIONID'])
        uid = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=uid)
        request.user = user
    except:
        return_404_response()


@csrf_exempt
@transaction.atomic
def api_user_create(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif request.META['CONTENT_TYPE'] == 'application/json':
        data = simplejson.loads(request.body)
        username = data.POST.get(u'username', None)
        password = data.POST.get(u'password', None)
        repeatPwd = data.POST.get(u'repeatPwd', None)
        mobile = data.POST.get(u'mobile', None)
        email = data.POST.get(u'email', None)
        community_id = data.POST.get(u'community', None)
        is_admin = data.POST.get(u'is_admin', None)
        floor = data.POST.get(u'floor', None)
        gate_card = data.POST.get(u'gate_card', None)
        address = data.POST.get(u'address', None)
        if len(User.objects.filter(username=username)) > 0:
            response_data = {'username_error': True, 'info': u'用户名已存在'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if password != repeatPwd:
            response_data = {'password_error': True, 'info': u'两次密码输入不相同'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        pattern = re.compile(r'^[a-zA-Z0-9]{6,15}$')
        if not pattern.match(password):
            response_data = {'password_error': True, 'info': u'密码：字母、数字组成，6-15位'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        pattern = re.compile(r'^(1[0-9][0-9])\d{8}$')
        if not pattern.match(mobile):
            response_data = {'mobile_error': True, 'info': u'请输入正确的手机号码'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if not validateEmail(email):
            response_data = {'email_error': True, 'info': u'请输入正确的邮箱地址'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        user = User(username=username)
        user.password = make_password(password, 'md5')
        user.email = email
        if is_admin == u'2':
            user.is_staff = True
        user.save()
        profile_detail = ProfileDetail(profile=user)
        profile_detail.phone_number = mobile
        community = Community.objects.get(id=community_id)
        profile_detail.community = community
        profile_detail.floor = floor
        profile_detail.gate_card = gate_card
        profile_detail.address = address
        profile_detail.is_admin = True if is_admin == u'1' else False
        profile_detail.save()
        return HttpResponse(simplejson.dumps({'info': 'create user successful'}), content_type='application/json')
    else:
        return return_404_response()


@csrf_exempt
def api_user_login(request):
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        username = data.get(u'username', None)
        password = data.get(u'password', None)
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth_login(request, user)
            profile = ProfileDetail.objects.get(profile=user)
            user_profile = list()
            data = {
                'username': user.username,
                'id': user.id,
                'community_id': profile.community.id,
                'community_name': profile.community.title,
                'phone_num': profile.phone_number,
                'email': user.email,
                'floor': profile.floor,
                'room': profile.gate_card,
                'address': profile.address
            }
            user_profile.append(data)
            if user.is_staff:
                response_data = {'identity': 'admin', 'info': 'login successful', 'user_profile': user_profile}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            elif profile.is_admin:
                response_data = {'identity': 'worker', 'info': 'login successful', 'user_profile':user_profile}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                response_data = {'identity': 'resident', 'info': 'login successful', 'user_profile':user_profile}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        else:
            return HttpResponse(simplejson.dumps({'info': 'login failed'}), content_type='application/json')
    else:
        return return_404_response()


@csrf_exempt
@transaction.atomic
def api_user_update(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        username = data.get(u'username', None)
        mobile = data.get(u'mobile', None)
        email = data.get(u'email', None)
        community_id = data.get(u'community', None)
        floor = data.get(u'floor', None)
        gate_card = data.get(u'gate_card', None)
        address = data.get(u'address', None)
        pattern = re.compile(r'^(1[0-9][0-9])\d{8}$')
        if not pattern.match(mobile):
            response_data = {'mobile_error': True, 'info': u'请输入正确的手机号码'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if not validateEmail(email):
            response_data = {'email_error': True, 'info': u'请输入正确的邮箱地址'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        user = request.user
        user.email = email
        user.save()
        profile_detail = ProfileDetail.objects.get(profile=user)
        community = Community.objects.get(id=community_id)
        profile_detail.community = community
        profile_detail.floor = floor
        profile_detail.gate_card = gate_card
        profile_detail.address = address
        profile_detail.save()
        return HttpResponse(simplejson.dumps({'info': 'update profile detail successful'}),
                            content_type='application/json')
    else:
        return return_404_response()


@csrf_exempt
@transaction.atomic
def api_user_change_password(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        old_password = data.get(u'old_password', None)
        new_password = data.get(u'new_password', None)
        repeat_password = data.get(u'repeat_password', None)
        user = request.user
        if new_password != repeat_password:
            response_data = {'error': True, 'info': u'两次密码不一致'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if check_password(old_password, user.password):
            pattern = re.compile('\w{6,15}')
            match = pattern.match(new_password)
            if not match:
                response_data = {'error': True, 'info': u'密码长度为6-15位数字或字母'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                user.password = make_password(new_password, 'md5')
                user.save()
                Session.objects.get(session_key=request.META['HTTP_SESSIONID']).delete()
                return HttpResponse(simplejson.dumps({'error': False, 'info': u'密码更新成功'}),
                                    content_type='application/json')
        else:
            response_data = {'error': True, 'info': u'旧密码不正确'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        return return_404_response()


@csrf_exempt
@transaction.atomic
def api_user_change_ios_password(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        old_password = data.get(u'old_password', None)
        new_password = data.get(u'new_password', None)
        repeat_password = data.get(u'repeat_password', None)
        user = request.user
        if new_password != repeat_password:
            response_data = {'error': True, 'info': u'两次密码不一致'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if check_password(old_password, user.password):
            pattern = re.compile('\w{6,15}')
            match = pattern.match(new_password)
            if not match:
                response_data = {'error': True, 'info': u'密码长度为6-15位数字或字母'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                user.password = make_password(new_password, 'md5')
                user.save()
                Session.objects.get(session_key=request.session._session_key).delete()
                return HttpResponse(simplejson.dumps({'error': False, 'info': u'密码更新成功'}),
                                    content_type='application/json')
        else:
            response_data = {'error': True, 'info': u'旧密码不正确'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        return return_404_response()

@transaction.atomic
@csrf_exempt
def api_user_delete(request):
    convert_session_id_to_user(request)

    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        pass


@csrf_exempt
def api_user_list(request):
    convert_session_id_to_user(request)

    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        user = request.user
        if not user.is_staff:
            return HttpResponse(simplejson.dumps({'error': True, 'info': u'仅限管理员访问'}), content_type='application/json')
        else:
            profile_detail_list = ProfileDetail.objects.all()
            response_data = list()
            for profile_detail in profile_detail_list:
                data = {
                    'id': profile_detail.profile.id,
                    'username': profile_detail.profile.username,
                    'phone_number': profile_detail.phone_number,
                    'email': profile_detail.profile.email,
                    'community': profile_detail.community.title,
                    'floor': profile_detail.floor,
                    'gate_card': profile_detail.gate_card,
                    'address': profile_detail.address
                }
                response_data.append(data)
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        return return_404_response()


def api_user_logout(request):
    auth_logout(request)
    return HttpResponse(simplejson.dumps({'info': u'成功登出'}), content_type='application/json')


@csrf_exempt
def api_get_worker_list(request):
    convert_session_id_to_user(request)
    community_id = request.GET.get("community_id", None)
    if community_id:
        community = Community.objects.get(id=community_id)
    else:
        response_data = {'info': '没有传入小区id', 'success': False}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    deal_person_list = ProfileDetail.objects.filter(is_admin=True, community=community)
    if deal_person_list:
        worker_list = list()
        for profile_detail in deal_person_list:
            data = {
                'id': profile_detail.profile.id,
                'username': profile_detail.profile.username,
                'phone_number': profile_detail.phone_number,
            }
            worker_list.append(data)
        response_data = {'worker_list': worker_list, 'success': True}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        return HttpResponse(simplejson.dumps({'success': False}), content_type='application/json')



@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def worker_statistics(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    all_worker = ProfileDetail.objects.filter(community=profile.community,is_admin=True)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    btn_style = request.GET.get("btn_style", None)
    year_and_month = request.POST.get("YearAndMonth",None)
    if year_and_month:
        now_year = int(str(year_and_month).split('-')[0])
        now_moth = int(str(year_and_month).split('-')[1])
    else:
        if datetime.datetime.now().month == 1:
            if datetime.datetime.now().day > 7:
                now_moth = 12
                now_year = datetime.datetime.now().year-1
            else:
                now_moth = 11
                now_year = datetime.datetime.now().year-1
        elif datetime.datetime.now().month == 2:
            if datetime.datetime.now().day < 7:
                now_moth = 12
                now_year = datetime.datetime.now().year-1
            else:
                now_moth = 1
                now_year = datetime.datetime.now().year
        else:
            if datetime.datetime.now().day > 7:
                now_moth = datetime.datetime.now().month-1
                now_year = datetime.datetime.now().year
            else:
                now_moth = datetime.datetime.now().month-2
                now_year = datetime.datetime.now().year
    worker_month_list = []
    for i in range(1,now_moth+1):
        for worker in all_worker:
            deal_complains_num = Complaints.objects.filter(complete_date__year=now_year, complete_date__month=i,handler=worker.profile).count()
            pleasure_complains_num = Complaints.objects.filter(complete_date__year=now_year, complete_date__month=i,pleased=1,handler=worker.profile).count()
            deal_repairs_num = Repair.objects.filter(complete_date__year=now_year, complete_date__month=i,handler=worker.profile).count()
            pleasure_repairs_num = Repair.objects.filter(complete_date__year=now_year, complete_date__month=i,pleased=1,handler=worker.profile).count()
            deal_express_num = Express.objects.filter(complete_date__year=now_year, complete_date__month=i,handler=worker).count()
            pleasure_express_num = Express.objects.filter(complete_date__year=now_year, complete_date__month=i,pleased=1,handler=worker).count()
            pleasure_comment_sum = pleasure_complains_num + pleasure_repairs_num + pleasure_express_num
            comment_sum = deal_complains_num + deal_repairs_num + deal_express_num
            if pleasure_comment_sum and comment_sum:
                pleasure_percent = "{0:.2%}".format(float(pleasure_comment_sum)/float(comment_sum))
            else:
                pleasure_percent = 0
            worker_month_statistics = {
                'deal_complains_num': deal_complains_num,
                'deal_repairs_num': deal_repairs_num,
                'deal_express_num': deal_express_num,
                'worker_name': worker.profile.username,
                'pleasure_comment_sum': pleasure_comment_sum,
                'pleasure_percent': pleasure_percent,
                'year_month': "" + str(now_year) + "." + str(i) + "",
            }
            worker_month_list.append(worker_month_statistics)
    if request.user.is_staff:
        return render_to_response('worker_statistics.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'worker_month_list': worker_month_list,
            'profile': profile,
            'is_admin': False,
            'btn_style': int(btn_style)
        })


def get_complain_month_data(now_moth, now_year):
    complain_months_list = list()
    for i in range(1, now_moth + 1):
        month_complains_num = Complaints.objects.filter(create_date__year=now_year, create_date__month=i).count()
        month_security_complains_num = Complaints.objects.filter(create_date__year=now_year, create_date__month=i,
                                                                 type='安全投诉').count()
        month_environment_complains_num = Complaints.objects.filter(create_date__year=now_year, create_date__month=i,
                                                                    type='环境投诉').count()
        month_employee_complains_num = Complaints.objects.filter(create_date__year=now_year, create_date__month=i,
                                                                 type='员工投诉').count()
        complain_month_statistics = {
            'month_complains_num': month_complains_num,
            'month_security_complains_num': month_security_complains_num,
            'month_environment_complains_num': month_environment_complains_num,
            'month_employee_complains_num': month_employee_complains_num,
            'year_month': "" + str(now_year) + "." + str(i) + "",
        }
        complain_months_list.append(complain_month_statistics)
    return complain_months_list


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def complain_statistics(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    btn_style = request.GET.get("btn_style", None)
    year_and_month = request.POST.get("YearAndMonth",None)
    if year_and_month:
        now_year = int(str(year_and_month).split('-')[0])
        now_moth = int(str(year_and_month).split('-')[1])
    else:
        now_moth = datetime.datetime.now().month
        now_year = datetime.datetime.now().year
    complain_months_list = get_complain_month_data(now_moth, now_year)
    if request.user.is_staff:
        return render_to_response('complain_statistics.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'profile': profile,
            'is_admin': False,
            'complain_months_list': complain_months_list,
            'btn_style': int(btn_style),
        })


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def express_statistics(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    btn_style = request.GET.get("btn_style", None)
    year_and_month = request.POST.get("YearAndMonth",None)
    if year_and_month:
        now_year = int(str(year_and_month).split('-')[0])
        now_moth = int(str(year_and_month).split('-')[1])
    else:
        now_moth = datetime.datetime.now().month
        now_year = datetime.datetime.now().year
    express_month_list = []
    for i in range(1,now_moth+1):
        month_express_num = Express.objects.filter(arrive_date__year=now_year, arrive_date__month=i).count()
        month_self_express_num = Express.objects.filter(arrive_date__year=now_year, arrive_date__month=i,type='2').count()
        month_send_express_num = Express.objects.filter(arrive_date__year=now_year, arrive_date__month=i,type='1').count()
        express_month_statistics = {
            'month_express_num': month_express_num,
            'month_self_express_num': month_self_express_num,
            'month_send_express_num': month_send_express_num,
            'year_month': "" + str(now_year) + "." + str(i) + "",
        }
        express_month_list.append(express_month_statistics)
    if request.user.is_staff:
        return render_to_response('express_statistics.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'profile': profile,
            'express_month_list': express_month_list,
            'is_admin': False,
            'btn_style': int(btn_style)
        })


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def repair_statistics(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    btn_style = request.GET.get("btn_style", None)
    year_and_month = request.POST.get("YearAndMonth",None)
    if year_and_month:
        now_year = int(str(year_and_month).split('-')[0])
        now_moth = int(str(year_and_month).split('-')[1])
    else:
        now_moth = datetime.datetime.now().month
        now_year = datetime.datetime.now().year
    repairs_month_list = []
    for i in range(1,now_moth+1):
        month_repairs_num = Repair.objects.filter(create_date__year=now_year, create_date__month=i).count()
        month_personal_repairs_num = Repair.objects.filter(create_date__year=now_year, create_date__month=i,type='个人报修').count()
        month_public_repairs_num = Repair.objects.filter(create_date__year=now_year, create_date__month=i,type='公共报修').count()
        repair_month_statistics = {
            'month_repairs_num': month_repairs_num,
            'month_personal_repairs_num': month_personal_repairs_num,
            'month_public_repairs_num': month_public_repairs_num,
            'year_month': "" + str(now_year) + "." + str(i) + "",
        }
        repairs_month_list.append(repair_month_statistics)
    if request.user.is_staff:
        return render_to_response('repair_statistics.html', {
            'show': True,
            'community': one_community,
            'change_community': status,
            'user': request.user,
            'communities': communities,
            'profile': profile,
            'is_admin': False,
            'repairs_month_list': repairs_month_list,
            'btn_style': int(btn_style)
        })

@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def modify_property_fee(request):
    new_fee = request.POST.get('new_fee',None)
    fee_standard = Fee_standard.objects.filter(type='物业费')
    if fee_standard:
        fee_standard[0].fee = new_fee
        fee_standard[0].save()
    else:
        fee_standard = Fee_standard()
        fee_standard.type = '物业费'
        fee_standard.fee = new_fee
        fee_standard.save()
    response_data = {'success': True,'info':'修改成功'}
    return HttpResponse(simplejson.dumps(response_data),content_type='application/json')


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def modify_property_deadline(request):
    new_deadline = request.POST.get('remind_time',None)
    fee_standard = Fee_standard.objects.filter(type='物业费')
    now_year = datetime.datetime.now().year
    #new_deadline = remind_time.split('-')
    #new_deadline = datetime.date(int(new_deadline[0]),int(new_deadline[1]),int(new_deadline[2]))
    if fee_standard:
        #fee_standard[0].remind_time = remind_time
        fee_standard[0].deadline = new_deadline
        property_fee = Property_fee.objects.filter(pay_date__year=now_year)
        for property_single in property_fee:
            property_single.deadline = new_deadline
            property_single.save()
        fee_standard[0].save()
    else:
        fee_standard = Fee_standard()
        fee_standard.type = '物业费'
        fee_standard.deadline = new_deadline
        fee_standard.save()
    response_data = {'success': True,'info':'修改成功'}
    return HttpResponse(simplejson.dumps(response_data),content_type='application/json')



@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def urge_paying(request):
    user_id = request.POST.get('user_id',None)
    user_obj = User.objects.get(id=user_id)
    profile = ProfileDetail.objects.get(profile=user_obj)
    description = "您本年的物业费没交请及时缴纳"
    title = '物业费'
    theme = '亨通物业温馨提示'
    role = '管理员通知'
    now_year = datetime.datetime.now().year
    if profile.device_user_id and profile.device_chanel_id and profile.device_type:
        push_class = ThreadClass(description, profile, title, theme, role)
        push_class.start()
        response_data = {'info': '催费成功', 'success': True}
        property_fee = Property_fee.objects.filter(author=profile,deadline__year=now_year)
        property_fee[0].send_message = 1
        property_fee[0].save()
        response_data = {'info': '催缴成功','success': True}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
         response_data = {'info': '该用户没有绑定手机端，催费失败','success': False}
         return HttpResponse(simplejson.dumps(response_data), content_type='application/json')

