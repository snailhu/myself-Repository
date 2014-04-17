#coding:utf-8
import re
import logging
import datetime
import uuid
from captcha.helpers import captcha_image_url
import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth import authenticate, login as auth_login
from django.core import serializers
from captcha.models import CaptchaStore
from django.contrib.sessions.models import Session
from SmartDataApp.forms import UserForm
from SmartDataApp.models import Picture, ProfileDetail, Community, Complaints, Housekeeping, Express, Repair,Wallet
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from email.header import Header

def validateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

class UTC(datetime.tzinfo):
    def __init__(self,offset = 0):
        self._offset = offset

    def utcoffset(self, dt):
        return datetime.timedelta(hours=self._offset)

    def tzname(self, dt):
        return "UTC +%s" % self._offset

    def dst(self, dt):
        return datetime.timedelta(hours=self._offset)



def random_captcha():
    response_data = {}
    response_data['cptch_key'] = CaptchaStore.generate_key()
    response_data['cptch_image'] = captcha_image_url(response_data['cptch_key'])
    return response_data


def generate_captcha(request):
    response_data = random_captcha()
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


def index(request):
    communities = Community.objects.all()
    if request.user.is_authenticated():
        profile = ProfileDetail.objects.get(profile=request.user)
        if request.user.is_staff:
            return render_to_response('admin_index.html', {'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2})
        elif profile.is_admin:
            return render_to_response('work_index.html', {'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2})
        else:
            return render_to_response('index.html', {'user': request.user, 'communities': communities, 'profile': profile, 'change_community': 2})
    else:
        return render_to_response('index.html', {'communities': communities})


@login_required
def own_information(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    wallet = Wallet.objects.filter(user_profile=profile)
    if wallet:
        wallet = wallet[0]
    if profile:
        return render_to_response('own_information.html', {'user': request.user, 'profile': profile,'wallet':wallet  })
    else:
        return render_to_response('index.html')


@login_required
def dashboard(request):
    return render_to_response('dashboard.html', {
        'username': request.user.username
    })


def multi_response(flag, success, info, template):
    if flag:
        response_data = {'success': success, 'info': info}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        response_data = {'success': success, 'info': info}
        return render_to_response(template, response_data)


@transaction.atomic
@csrf_exempt
def register_old(request):
    if request.method == 'GET':
        response_data = {'success': True}
        response_data.update(csrf(request))
        return render_to_response('register_old.html', response_data)
    elif request.method == 'POST':
        flag = False
        email, username, password = None, None, None
        if request.META['CONTENT_TYPE'] == 'application/json':
            data = simplejson.loads(request.body)
            email = data.get(u'email', None)
            username = data.get(u'username', None)
            password = data.get(u'password', None)
            flag = True
        else:
            email = request.POST.get(u'email', None)
            username = request.POST.get(u'username', None)
            password = request.POST.get(u'password', None)
        if email and username and password:
            pattern = re.compile('\w{6,15}')
            match = pattern.match(password)
            if not match:
                return multi_response(flag, False, '密码长度为6-15位数字或字母', 'register_old.html')
            if len(User.objects.filter(username=username)) > 0:
                return multi_response(flag, False, '该用户名已经存在', 'register_old.html')
            if len(User.objects.filter(email=email)) > 0:
                return multi_response(flag, False, '该邮箱已经存在', 'register_old.html')
            user = User.objects.get_or_create(username=username)[0]
            if password:
                user.password = make_password(password, 'md5')
            if email:
                user.email = email
            user.save()
            logging.info("user %s, userid %s register success" % (username, user.id))
            user = authenticate(username=username, password=password)
            if flag:
                response_data = {'success': True}
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            else:
                if user is not None:
                    if user.is_active:
                        auth_login(request, user)
                    else:
                        return redirect(index)
        return redirect(dashboard)


@transaction.atomic
@csrf_exempt
def new_register(request):
    mobile = False
    if request.META['CONTENT_TYPE'] == 'application/json':
        mobile = True
    if request.method == u'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.data.get('username', None)
            password = form.data.get('password', None)
            email = form.data.get('username', None)
            user = User.objects.get_or_create(username=username)[0]
            user.password = make_password(password, 'md5')
            user.email = email
            user.save()
            phone_number = form.data.get('phone_number', None)
            profile = ProfileDetail.objects.get_or_create(profile=user)[0]
            profile.phone_number = phone_number
            profile.save()
            logging.info("user %s, userid %s register success" % (username, user.id))
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    if mobile:
                        response_data = {'success': True}
                        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
                    else:
                        return redirect(dashboard)
                else:
                    return redirect(index)
            else:
                if mobile:
                    response_data = {'success': False}
                    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:
            response_data = {'success': True, 'form': form}
            response_data.update(csrf(request))
            return render_to_response('register_old.html', response_data)
    else:
        form = UserForm()
        response_data = {'success': True, 'form': form}
        response_data.update(csrf(request))
        return render_to_response('register_old.html', response_data)


@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def profile(request):
    if request.method == 'GET':
        return render_to_response('profile.html', {
            'username': request.user.username,
            'init': True
        })
    elif request.method == 'POST':
        flag = False
        old_password, new_password, new_password_again = None, None, None
        if request.META['CONTENT_TYPE'] == 'application/json':
            data = simplejson.loads(request.body)
            old_password = data.get(u'old_password', None)
            new_password = data.get(u'new_password', None)
            new_password_again = data.get(u'new_password_again', None)
            flag = True
        else:
            old_password = request.POST.get(u'old_password', None)
            new_password = request.POST.get(u'new_password', None)
            new_password_again = request.POST.get(u'new_password_again', None)
        if old_password and new_password and new_password_again:
            user = request.user
            if old_password:
                if check_password(old_password, user.password):
                    pattern = re.compile('\w{6,15}')
                    match = pattern.match(new_password)
                    if not match:
                        multi_response(flag, True, '密码长度为6-15位数字或字母', 'profile.html')
                    if new_password == new_password_again:
                        user.password = make_password(new_password, 'md5')
                        user.save()
                    else:
                        return render_to_response('profile.html', {
                            'username': user.username,
                            'success': False,
                            'info': '两次密码输入不正确!'
                        })
                else:
                    if flag:
                        response_data = {'success': False, 'info': '密码不正确'}
                        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
                    else:
                        return render_to_response('profile.html', {
                            'username': user.username,
                            'success': False,
                            'info': '密码不正确!'
                        })
            logging.info("user %s, userid %s change password success" % (user.username, user.id))
            if flag:
                response_data = {'success': True, 'info': '密码修改成功!'}
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            else:
                return render_to_response('profile.html', {
                    'username': user.username,
                    'success': True,
                    'info': '密码修改成功!'
                })


@csrf_exempt
def login_old(request):
    if request.method != 'POST':
        return redirect(index)
    elif request.method == 'POST':
        flag = False
        username, password = None, None
        if request.META['CONTENT_TYPE'] == 'application/json':
            data = simplejson.loads(request.body)
            username = data.get(u'username', None)
            password = data.get(u'password', None)
            flag = True
        else:
            username = request.POST.get(u'username', None)
            password = request.POST.get(u'password', None)

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                if flag:
                    response_data = {'success': True, 'user_id': user.id}
                    return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
                else:
                    return redirect(dashboard)
        else:
            if flag:
                response_data = {'success': False, 'info': '用户不存在'}
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            else:
                return render_to_response('index_old.html', {"hide": False})


def shine(request):
    user = request.user
    username = user.username if user.id else None
    pictures = list(Picture.objects.all().order_by('-timestamp_add'))
    order = request.GET.get('order', None)
    if order == u'like':
        pictures = list(Picture.objects.all().order_by('-like'))
    elif order == u'keep':
        pictures = list(Picture.objects.all().order_by('-keep'))
    mobile = request.GET.get('mobile', None)
    if mobile:
        pictures = serializers.serialize("json", pictures)
        response_data = {'username': username, 'pictures': pictures, 'user_id': user.id}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    return render_to_response('shine.html', {
        'username': username,
        'pictures': pictures,
        'user': user
    })


@csrf_exempt
@transaction.atomic
@login_required
def ajax_upload_image(request):
    if request.method == 'POST':
        upload_src = request.FILES.get('upload_img', None)
        comment = request.POST.get('introduction', None)
        if upload_src is None:
            response_data = {'success': False, 'info': '上传图片不存在！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        name = upload_src.name
        pic_objects = Picture.objects.filter(title=name)
        if len(pic_objects) > 0:
            response_data = {'success': False, 'info': '图片已存在！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        pic = Picture(author=request.user)
        pic.src = upload_src
        pic.comment = comment
        pic.title = upload_src.name
        pic.save()
        response_data = {'success': True, 'info': '图片上传成功！'}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        response_data = {'success': False, 'info': '仅接受POST请求！'}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@login_required
@csrf_exempt
@transaction.atomic
def ajax_like(request, id=None):
    if request.method == 'POST' and id:
        picture = Picture.objects.get(id=id)
        picture.like += 1
        picture.save()
        response_data = {'success': True, 'info': '感谢您喜欢这张图片！', 'like': picture.like}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        response_data = {'success': False, 'info': '仅接受POST请求！'}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@login_required
@csrf_exempt
@transaction.atomic
def ajax_keep(request, id=None):
    #TODO: like function not completed.
    if request.method == 'POST' and id:
        picture = Picture.objects.get(id=id)
        user = request.user
        profile_detail = ProfileDetail.objects.get_or_create(profile=user)[0]
        if picture not in profile_detail.pictures.all():
            picture.keep += 1
            picture.save()
            profile_detail.pictures.add(picture)
            profile_detail.save()
        response_data = {'success': True, 'info': '感谢您喜欢收藏图片！', 'keep': picture.keep}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        response_data = {'success': False, 'info': '仅接受POST请求！'}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@transaction.atomic
@csrf_exempt
@login_required
def ajax_delete_picture(request, id=None):
    if request.method == 'POST' and id:
        picture = Picture.objects.get(id=id)
        current_user = request.user
        if current_user == picture.author or current_user.is_staff:
            picture.delete()
            response_data = {'success': True, 'info': '删除成功！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:
            response_data = {'success': True, 'info': '非作者，不能删除！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
        response_data = {'success': False, 'info': '仅接受POST请求！'}
        return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


def get_message_num(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    if request.user.is_staff:
        complain = Complaints.objects.filter(is_admin_read=True)
        complain_num = complain.count()
        repair = Repair.objects.filter(is_admin_read=True)
        repair_num = repair.count()
        housekeeping = Housekeeping.objects.filter(is_admin_read=True)
        housekeeping_num = housekeeping.count()
        express_num = 0
        sum_num = complain_num + repair_num + housekeeping_num + express_num
        return complain_num, express_num, housekeeping_num, repair_num, sum_num
    elif profile.is_admin:
        complain = Complaints.objects.filter(is_worker_read=True)
        complain_num = complain.count()
        repair = Repair.objects.filter(is_worker_read=True)
        repair_num = repair.count()
        housekeeping = Housekeeping.objects.filter(is_worker_read=True)
        housekeeping_num = housekeeping.count()
        express = Express.objects.filter(is_worker_read=True)
        express_num = express.count()
        sum_num = complain_num + repair_num + housekeeping_num + express_num
        return complain_num, express_num, housekeeping_num, repair_num, sum_num
    else:
        profile = ProfileDetail.objects.get(profile=request.user)
        complain = Complaints.objects.filter(author=request.user.username, is_read=True)
        complain_num = complain.count()
        repair = Repair.objects.filter(author=request.user.username, is_read=True)
        repair_num = repair.count()
        housekeeping = Housekeeping.objects.filter(author=profile, is_read=True)
        housekeeping_num = housekeeping.count()
        express = Express.objects.filter(author=profile, is_read=True)
        express_num = express.count()
        sum_num = complain_num + repair_num + housekeeping_num + express_num
        return complain_num, express_num, housekeeping_num, repair_num, sum_num


@transaction.atomic
@csrf_exempt
@login_required
def get_new_dynamic_data(request):
    complain_num, express_num, housekeeping_num, repair_num, sum_num = get_message_num(request)
    response_data = {'complain_num': complain_num, 'repair_num': repair_num, 'housekeeping_num': housekeeping_num,
                     'express_num': express_num, 'sum_num': sum_num}
    return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


def get_house_data(house_keep_list, housekeeping_detail):
    local = housekeeping_detail.time.astimezone(UTC(8))
    data = {
        'id': housekeeping_detail.id,
        'housekeeping_author': str(housekeeping_detail.author.profile),
        'content': housekeeping_detail.housekeeping_item.content,
        'housekeeping_status': housekeeping_detail.status,
        'price_description': housekeeping_detail.housekeeping_item.price_description,
        'item': housekeeping_detail.housekeeping_item.item,
        'remarks': housekeeping_detail.housekeeping_item.remarks,
        'pleased': housekeeping_detail.pleased,
        'handler': str(housekeeping_detail.handler),
        'time': str(local).split('.')[0]
    }
    house_keep_list.append(data)


def get_compalin_data(complain_detail, complain_list):
    local = complain_detail.timestamp.astimezone(UTC(8))
    data = {
        'id': complain_detail.id,
        'complain_author': complain_detail.author,
        'content': complain_detail.content,
        'type': complain_detail.type,
        'deal_status': complain_detail.status,
        'pleased': complain_detail.pleased,
        'src': complain_detail.src.name,
        'time': str(local).split('.')[0],
        'handler': str(complain_detail.handler)
    }
    complain_list.append(data)


def get_repair_data(repair_detail, repair_list):
    local = repair_detail.timestamp.astimezone(UTC(8))
    data = {
        'id': repair_detail.id,
        'repair_author': repair_detail.author,
        'content': repair_detail.content,
        'type': repair_detail.type,
        'deal_status': repair_detail.status,
        'pleased': repair_detail.pleased,
        'src': repair_detail.src.name,
        'time': str(local).split('.')[0],
        'handler': str(repair_detail.handler)
    }
    repair_list.append(data)


def get_express_data(express_detail, express_list):
    local_arrive = express_detail.arrive_time.astimezone(UTC(8))
    local_get = express_detail.get_time.astimezone(UTC(8))
    data = {
        'id': express_detail.id,
        'express_author': express_detail.author.profile.username,
        'get_express_type': express_detail.type,
        'deal_status': express_detail.status,
        'pleased': express_detail.pleased,
        'arrive_time': str(local_arrive).split('.')[0],
        'get_time': str(local_get).split('.')[0]
    }
    express_list.append(data)


@transaction.atomic
@csrf_exempt
@login_required
def get_detail_data(request):
    if request.method != 'POST':
        return redirect(index)
    else:
        item_name = request.POST.get('item_name', None)
        profile = ProfileDetail.objects.get(profile=request.user)
        if item_name == u'housekeeping':
            house_keep_list = list()
            if request.user.is_staff:
                housekeeping = Housekeeping.objects.all().order_by('-time')
                for housekeeping_detail in housekeeping:
                    housekeeping_detail.is_admin_read = False
                    housekeeping_detail.save()
                    get_house_data(house_keep_list, housekeeping_detail)
                response_data = {'house_keep_list': house_keep_list, 'success': True, 'identity': 'admin'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            elif profile.is_admin:
                housekeeping = Housekeeping.objects.filter(handler=request.user).order_by('-time')
                for housekeeping_detail in housekeeping:
                    housekeeping_detail.is_worker_read = False
                    housekeeping_detail.save()
                    get_house_data(house_keep_list, housekeeping_detail)
                response_data = {'house_keep_list': house_keep_list, 'success': True, 'identity': 'worker'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                housekeeping = Housekeeping.objects.filter(author=profile).order_by('-time')
                for housekeeping_detail in housekeeping:
                    housekeeping_detail.is_read = False
                    housekeeping_detail.save()
                    get_house_data(house_keep_list, housekeeping_detail)
                response_data = {'house_keep_list': house_keep_list, 'success': True, 'identity': 'inhabitant'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if item_name == u'complain':
            complain_list = list()
            if request.user.is_staff:
                complain = Complaints.objects.all().order_by('-timestamp')
                for complain_detail in complain:
                    complain_detail.is_admin_read = False
                    complain_detail.save()
                    get_compalin_data(complain_detail, complain_list)
                response_data = {'complain_list': complain_list, 'success': True, 'identity': 'admin'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            elif profile.is_admin:
                complain = Complaints.objects.filter(handler=request.user).order_by('-timestamp')
                for complain_detail in complain:
                    complain_detail.is_worker_read = False
                    complain_detail.save()
                    get_compalin_data(complain_detail, complain_list)
                response_data = {'complain_list': complain_list, 'success': True, 'identity': 'worker'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                complain = Complaints.objects.filter(author=request.user.username).order_by('-timestamp')
                for complain_detail in complain:
                    complain_detail.is_read = False
                    complain_detail.save()
                    get_compalin_data(complain_detail, complain_list)
                response_data = {'complain_list': complain_list, 'success': True, 'identity': 'inhabitant'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')

        if item_name == u'express':
            express_list = list()
            if request.user.is_staff:
                express = Express.objects.all().order_by('-arrive_time')
                for express_detail in express:
                    express_detail.is_read = False
                    express_detail.save()
                    get_express_data(express_detail, express_list)
                response_data = {'express_list': express_list, 'success': True, 'identity': 'admin'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            elif profile.is_admin:
                express = Express.objects.all().order_by('-arrive_time')
                for express_detail in express:
                    express_detail.is_read = False
                    express_detail.save()
                    get_express_data(express_detail, express_list)
                response_data = {'express_list': express_list, 'success': True, 'identity': 'worker'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                express = Express.objects.filter(author=profile).order_by('-arrive_time')
                for express_detail in express:
                    express_detail.is_read = False
                    express_detail.save()
                    get_express_data(express_detail, express_list)
                response_data = {'express_list': express_list, 'success': True, 'identity': 'inhabitant'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        if item_name == u'repair':
            repair_list = list()
            if request.user.is_staff:
                repair = Repair.objects.all().order_by('-timestamp')
                for repair_detail in repair:
                    repair_detail.is_admin_read = False
                    repair_detail.save()
                    get_repair_data(repair_detail, repair_list)
                response_data = {'repair_list': repair_list, 'success': True, 'identity': 'admin'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            elif profile.is_admin:
                repair = Repair.objects.filter(handler=request.user).order_by('-timestamp')
                for repair_detail in repair:
                    repair_detail.is_worker_read = False
                    repair_detail.save()
                    get_repair_data(repair_detail, repair_list)
                response_data = {'repair_list': repair_list, 'success': True, 'identity': 'admin'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                repair = Repair.objects.filter(author=request.user.username).order_by('-timestamp')
                for repair_detail in repair:
                    repair_detail.is_read = False
                    repair_detail.save()
                    get_repair_data(repair_detail, repair_list)
                response_data = {'repair_list': repair_list, 'success': True, 'identity': 'admin'}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


@transaction.atomic
@csrf_exempt
def api_get_dynamic_data_num(request):
    convert_session_id_to_user(request)
    complain_num, express_num, housekeeping_num, repair_num, sum_num = get_message_num(request)
    response_data = {'complain_num': complain_num, 'repair_num': repair_num, 'housekeeping_num': housekeeping_num,
                     'express_num': express_num, 'sum_num': sum_num}
    return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


@transaction.atomic
@csrf_exempt
def api_get_dynamic_data(request):
    convert_session_id_to_user(request)
    item_name = request.POST.get('item_name', None)
    profile = ProfileDetail.objects.get(profile=request.user)
    if item_name == u'housekeeping':
        house_keep_list = list()
        if request.user.is_staff:
            housekeeping = Housekeeping.objects.filter(is_admin_read=True).order_by('-time')
            for housekeeping_detail in housekeeping:
                housekeeping_detail.is_admin_read = False
                housekeeping_detail.save()
                get_house_data(house_keep_list, housekeeping_detail)
            response_data = {'house_keep_list': house_keep_list, 'success': True, 'identity': 'admin'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        elif profile.is_admin:
            housekeeping = Housekeeping.objects.filter(handler=request.user, is_worker_read=True).order_by('-time')
            for housekeeping_detail in housekeeping:
                housekeeping_detail.is_worker_read = False
                housekeeping_detail.save()
                get_house_data(house_keep_list, housekeeping_detail)
            response_data = {'house_keep_list': house_keep_list, 'success': True, 'identity': 'worker'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        else:
            housekeeping = Housekeeping.objects.filter(author=profile, is_read=True).order_by('-time')
            for housekeeping_detail in housekeeping:
                housekeeping_detail.is_read = False
                housekeeping_detail.save()
                get_house_data(house_keep_list, housekeeping_detail)
            response_data = {'house_keep_list': house_keep_list, 'success': True, 'identity': 'inhabitant'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    if item_name == u'complain':
        complain_list = list()
        if request.user.is_staff:
            complain = Complaints.objects.filter(is_admin_read=True).order_by('-timestamp')
            for complain_detail in complain:
                complain_detail.is_admin_read = False
                complain_detail.save()
                get_compalin_data(complain_detail, complain_list)
            response_data = {'complain_list': complain_list, 'success': True, 'identity': 'admin'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        elif profile.is_admin:
            complain = Complaints.objects.filter(handler=request.user, is_worker_read=True).order_by('-timestamp')
            for complain_detail in complain:
                complain_detail.is_worker_read = False
                complain_detail.save()
                get_compalin_data(complain_detail, complain_list)
            response_data = {'complain_list': complain_list, 'success': True, 'identity': 'worker'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        else:
            complain = Complaints.objects.filter(author=request.user.username, is_read=True).order_by('-timestamp')
            for complain_detail in complain:
                complain_detail.is_read = False
                complain_detail.save()
                get_compalin_data(complain_detail, complain_list)
            response_data = {'complain_list': complain_list, 'success': True, 'identity': 'inhabitant'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')

    if item_name == u'express':
        express_list = list()
        if request.user.is_staff:
            express = Express.objects.all(is_admin_read=True).order_by('-arrive_time')
            for express_detail in express:
                express_detail.is_read = False
                express_detail.save()
                get_express_data(express_detail, express_list)
            response_data = {'express_list': express_list, 'success': True, 'identity': 'admin'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        elif profile.is_admin:
            express = Express.objects.all(is_admin_read=True).order_by('-arrive_time')
            for express_detail in express:
                express_detail.is_read = False
                express_detail.save()
                get_express_data(express_detail, express_list)
            response_data = {'express_list': express_list, 'success': True, 'identity': 'worker'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        else:
            express = Express.objects.filter(author=profile, is_read=True).order_by('-arrive_time')
            for express_detail in express:
                express_detail.is_read = False
                express_detail.save()
                get_express_data(express_detail, express_list)
            response_data = {'express_list': express_list, 'success': True, 'identity': 'inhabitant'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    if item_name == u'repair':
        repair_list = list()
        if request.user.is_staff:
            repair = Repair.objects.all(is_admin_read=True).order_by('-timestamp')
            for repair_detail in repair:
                repair_detail.is_admin_read = False
                repair_detail.save()
                get_repair_data(repair_detail, repair_list)
            response_data = {'repair_list': repair_list, 'success': True, 'identity': 'admin'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        elif profile.is_admin:
            repair = Repair.objects.filter(handler=request.user, is_worker_read=True).order_by('-timestamp')
            for repair_detail in repair:
                repair_detail.is_worker_read = False
                repair_detail.save()
                get_repair_data(repair_detail, repair_list)
            response_data = {'repair_list': repair_list, 'success': True, 'identity': 'admin'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        else:
            repair = Repair.objects.filter(author=request.user.username, is_read=True).order_by('-timestamp')
            for repair_detail in repair:
                repair_detail.is_read = False
                repair_detail.save()
                get_repair_data(repair_detail, repair_list)
            response_data = {'repair_list': repair_list, 'success': True, 'identity': 'admin'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        response_data = {'success': False}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


def index_test(request):
    return render_to_response('index_test.html')

def shop_basic_service(request):
    return render_to_response('shop_basic_service.html')

def shop_cloud(request):
    return render_to_response('shop_cloud.html')

def shop_group(request):
    return render_to_response('shop_group.html')

def shop_phone(request):
    return render_to_response('shop_phone.html')

def shop_telephone(request):
    return render_to_response('shop_telephone.html')

def shop_tape(request):
    return render_to_response('shop_tape.html')

def supermarket(request):
    return render_to_response('supermarket.html')
@csrf_exempt
def forget_password(request):
    login_email = request.POST.get("login_email", None)
    if login_email:
        if validateEmail(login_email):
            user_obj = User.objects.filter(email=login_email)
            if user_obj:
                fromadrr = "HT_property@126.com"
                toadrr = ""+login_email+""
                msg = MIMEMultipart()
                msg['From'] = fromadrr
                msg['To']= ";".join(toadrr)
                msg['Subject']=Header(u'你的新密码 ')
                new_pwd = str(uuid.uuid4())[-6:]
                body = ""+new_pwd+""
                msg.attach(MIMEText(body,'plain','utf-8'))
                server = smtplib.SMTP('smtp.126.com','25')
                # server.login("dongshiyue1009@qq.com","")
                server.login('HT_property@126.com', 'htproperty')
                try:
                    server.sendmail(fromadrr, toadrr,msg.as_string())
                except Exception ,e:
                    print e
                server.quit()
                user_obj[0].password = make_password(new_pwd, 'md5')
                user_obj[0].save()
                response_data = {'success': True}
                return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
            else:
                return render_to_response('forget.html', {'show': True})
        else:
            return render_to_response('forget.html', {'email_error': True})
    else:
      return render_to_response('forget.html')

def local(request):
    return render_to_response('local.html')

