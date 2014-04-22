#coding:utf-8
import threading
import time
import datetime
import json
from urllib import unquote
from django.contrib.sessions.models import Session
from django.db.models import Q
from django.http import HttpResponse, HttpRequest
import requests
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
from SmartDataApp.models import Complaints, Repair, Express
from SmartDataApp.pusher.Channel import Channel
from SmartDataApp.views import index
from SmartDataApp.models import ProfileDetail, Community,Wallet
import hashlib

apiKey = "xS8MeH5f4vfgTukMcB2Bo6Ea"
secretKey = "chcxUOTIvBkItk91bXbXxQw5VSAaYhBb"

class UTC(datetime.tzinfo):
    def __init__(self,offset = 0):
        self._offset = offset

    def utcoffset(self, dt):
        return datetime.timedelta(hours=self._offset)

    def tzname(self, dt):
        return "UTC +%s" % self._offset

    def dst(self, dt):
        return datetime.timedelta(hours=self._offset)


def return_error_response():
    response_data = {'error': 'Just support POST method.'}
    return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


def return_404_response():
    return HttpResponse('', content_type='application/json', status=404)


@csrf_exempt
@login_required(login_url='/login/')
def complain(request):
    profile = ProfileDetail.objects.get(profile=request.user)
    community_id = request.session.get('community_id', profile.community.id)
    one_community = Community.objects.get(id=community_id)
    status = None
    if community_id == profile.community.id:
        status = 2
    else:
        status = 1
    communities = Community.objects.all()
    deal_status = request.GET.get("deal_status", None)
    if request.user.is_staff:
        if deal_status == u'1':
            complains = Complaints.objects.filter(community=one_community, status=1).order_by('-timestamp')
            btn_status = 1
        elif deal_status == u'2':
            complains = Complaints.objects.filter(community=one_community, status=2).order_by('-timestamp')
            btn_status = 2
        elif deal_status == u'3':
            complains = Complaints.objects.filter(community=one_community, status=3).order_by('-timestamp')
            btn_status = 3
        elif deal_status == u'4':
            complains = Complaints.objects.filter(community=one_community, status=4).order_by('-timestamp')
            btn_status = 4
        else:
            complains = Complaints.objects.filter(community=one_community, status=1).order_by('-timestamp')
            btn_status = 1
        deal_person_list = ProfileDetail.objects.filter(is_admin=True, community=one_community)
        if len(complains) > 0:
            paginator = Paginator(complains, 4)
            page = request.GET.get('page')
            try:
                complains_list = paginator.page(page)
            except PageNotAnInteger:
                complains_list = paginator.page(1)
            except EmptyPage:
                complains_list = paginator.page(paginator.num_pages)
            return render_to_response('admin_complains.html', {
                'complains': complains_list,
                'btn_style': btn_status,
                'show': True,
                'community': one_community,
                'change_community': status,
                'user': request.user,
                'deal_person_list': deal_person_list,
                'communities': communities,
                'profile': profile,
                'is_admin': False
            })
        else:
            return render_to_response('admin_complains.html', {
                'show': False,
                'user': request.user,
                'btn_style': btn_status,
                'deal_person_list': deal_person_list,
                'community': one_community,
                'communities': communities,
                'change_community': status,
                'profile': profile,
                'is_admin': False
            })
    elif profile.is_admin:
        if deal_status == u'2':
            complains = Complaints.objects.filter(handler=request.user, status=2).order_by('-timestamp')
            btn_status = 2
        elif deal_status == u'3':
            complains = Complaints.objects.filter(handler=request.user, status=3).order_by('-timestamp')
            btn_status = 3
        elif deal_status == u'4':
            complains = Complaints.objects.filter(handler=request.user, status=4).order_by('-timestamp')
            btn_status = 4
        else:
            complains = Complaints.objects.filter(handler=request.user, status=4).order_by('-timestamp')
            btn_status = 4
        if len(complains) > 0:
            paginator = Paginator(complains, 4)
            page = request.GET.get('page')
            try:
                complains_list = paginator.page(page)
            except PageNotAnInteger:
                complains_list = paginator.page(1)
            except EmptyPage:
                complains_list = paginator.page(paginator.num_pages)
            return render_to_response('worker_complains.html', {
                'complains': complains_list,
                'btn_style': btn_status,
                'show': True,
                'profile': profile,
                'communities': communities,
                'community': one_community,
                'change_community': status,
                'user': request.user,
                'is_admin': True
            })
        else:
            return render_to_response('worker_complains.html', {
                'show': False,
                'btn_style': btn_status,
                'communities': communities,
                'profile': profile,
                'community': one_community,
                'change_community': status,
                'user': request.user,
                'is_admin': True
            })
    else:
        return render_to_response('complains.html',
                                  {'user': request.user, 'profile': profile, 'communities': communities,
                                   'community': one_community, 'change_community': status})

class CheckAdminClass(threading.Thread):
    def __init__(self,item,admin,theme,id):
      threading.Thread.__init__(self)
      self._item = item
      self._admin = admin
      self._theme = theme
      self._id = id
    def get_item(self):
        if self._theme == '投诉':
            check_item = Complaints.objects.get(id=self._id)
        elif self._theme == '报修':
            check_item = Repair.objects.get(id=self._id)
        else:
            check_item = Express.objects.get(id=self._id)
        return check_item

    def check_status(self):
        check_item = self.get_item()
        if check_item.status ==1:
            payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':'15862396507','content':''+self._admin.profile.username+'未对'+self._theme+'申请做处理。'+str(datetime.datetime.now()).split('.')[0]+''}
            r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
            print r.text

    def run(self):
        payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':''+self._admin.phone_number+'','content':'您收到'+self._item.author+'的'+self._theme+'申请，请尽快处理。'+str(datetime.datetime.now()).split('.')[0]+''}
        r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
        print r.text
        time.sleep(120)
        check_item = self.get_item()
        if check_item.status ==1:
            try:
                  payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':''+self._admin.phone_number+'','content':'您收到'+self._item.author+'的'+self._theme+'申请，还未处理，请立即处理。'+str(datetime.datetime.now())+''}
                  r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
                  print r.text
                  check_thread = threading.Timer(120, self.check_status)
                  check_thread.start()
            except Exception ,e:
                print e
                payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':''+self._admin.phone_number+'','content':'您收到'+self._item.author+'的'+self._theme+'申请，还未处理，请立即处理。'+str(datetime.datetime.now())+''}
                r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
                print r.text
                check_thread.start()


@transaction.atomic
@csrf_exempt
def complain_create(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        profile = ProfileDetail.objects.get(profile=request.user)
        all_user_info = profile.community.profiledetail_set.all()
        community_admin = None
        for user_info in all_user_info:
            if user_info.profile.is_staff == True:
                community_admin = user_info
        communities = Community.objects.all()
        complain_content = request.POST.get('content', None)
        complain_type = request.POST.get('category', None)
        upload__complain_src = request.FILES.get('upload_complain_img', None)
        #complain_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        complain_time = datetime.datetime.now()
        profile = ProfileDetail.objects.get(profile=request.user)
        if complain_content or complain_type:
            complain = Complaints()
            complain.content = complain_content
            complain.timestamp = complain_time
            complain.create_date = complain_time
            complain.status = 1
            complain.author = request.user.username
            complain.author_detail = profile
            complain.type = complain_type
            complain.community = profile.community
            complain.is_admin_read = True
            if upload__complain_src:
                complain.src = upload__complain_src
            complain.save()
            check_admin = CheckAdminClass(complain,community_admin,'投诉',complain.id)
            check_admin.start()
            return render_to_response('complain_success.html',
                                      {'user': request.user, 'communities': communities, 'profile': profile,
                                       'change_community': 2})
        else:
            return render_to_response('complains.html',
                                      {'user': request.user, 'communities': communities, 'profile': profile,
                                       'change_community': 2})


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

class JudgeClass(threading.Thread):
  def __init__(self,item,theme,handler_profile):
      threading.Thread.__init__(self)
      self._item = item
      self._theme = theme
      self._handler_profile = handler_profile
  def run(self):
    try:
        if self._item.pleased != 1:
            payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':''+self._handler_profile.phone_number+'','content':''+self._item.author+'的'+self._theme+'服务被给与差评。'+str(datetime.datetime.now())+''}
            r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
            print r.text
    except Exception ,e:
        print e


class PleasedClass(threading.Thread):
  def __init__(self,item,id,theme):
      threading.Thread.__init__(self)
      self._item = item
      self._theme = theme
      self._id = id
  def get_item(self):
        if self._theme == '投诉':
            check_item = Complaints.objects.get(id=self._id)
        elif self._theme == '报修':
            check_item = Repair.objects.get(id=self._id)
        else:
            check_item = Express.objects.get(id=self._id)
        return check_item
  def check_pleased(self):
        check_item = self.get_item()
        if not check_item.pleased:
           check_item.pleased = 1
           check_item.save()
  def run(self):
    try:
        #check_thread = threading.Timer(60*24*7, self.check_pleased,)
        check_thread = threading.Timer(60, self.check_pleased,)
        check_thread.start()
    except Exception ,e:
        print e

class ThreadClass(threading.Thread):
  def __init__(self, description, handler_detail, title, theme, role):
      threading.Thread.__init__(self)
      self._description = description
      self._handler_detail = handler_detail
      self._title = title
      self._theme = theme
      self._role = role
  def run(self):
    try:
        push_message(self._description, self._handler_detail, self._title, self._theme, self._role)
    except Exception ,e:
        print e
        push_message(self._description, self._handler_detail, self._title, self._theme, self._role)

class PushCheckClass(threading.Thread):
  def __init__(self, description, handler_detail, title, theme, role, item,admin,id):
      threading.Thread.__init__(self)
      self._description = description
      self._handler_detail = handler_detail
      self._title = title
      self._theme = theme
      self._role = role
      self._item = item
      self._admin = admin
      self._id = id
  def get_item(self):
        if self._theme == '投诉':
            check_item = Complaints.objects.get(id=self._id)
        elif self._theme == '报修':
            check_item = Repair.objects.get(id=self._id)
        else:
            check_item = Express.objects.get(id=self._id)
        return check_item
  def check_status(self):
        check_item = self.get_item()
        if check_item.status == 4:#代表已受理但是工作人员还未处理
            payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':''+self._handler_detail.phone_number+'','content':'有新的任务没有接受，请立即登录平台查看!'+str(datetime.datetime.now())+''}
            r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
            check_thread = threading.Timer(90, self.check_status_again)
            check_thread.start()
  def check_status_again(self):
      check_item = self.get_item()
      if check_item.status == 4:
         payload = {'account': 'cf_xldkj' , 'password': 'sfi-server','mobile':''+self._admin.phone_number+'','content':'【变量】没有接受【变量】，请立即重新分配该任务。'+str(datetime.datetime.now())+''}
         r = requests.post("http://106.ihuyi.com/webservice/sms.php?method=Submit", data=payload)
         print r.text

  def run(self):
    try:
        push_message(self._description, self._handler_detail, self._title, self._theme, self._role)
        time.sleep(90)
        self.check_status()
    except Exception ,e:
        print e
        push_message(self._description, self._handler_detail, self._title, self._theme, self._role)
        time.sleep(90)
        self.check_status()

@transaction.atomic
@csrf_exempt
def complain_deal(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        admin = request.user
        admin_profile = ProfileDetail.objects.get(profile=admin)
        complain_array = request.POST.get("selected_complain_string", None)
        #handler_array = request.POST.get("selected_handler_string", None)
        deal_person_id = request.POST.get("deal_person_id", None)
        user_obj = User.objects.get(id=deal_person_id)
        handler_detail = ProfileDetail.objects.get(profile=user_obj)
        title = '消息通知'
        description = '你有新的投诉需要处理请查看！'
        theme = '投诉'
        role = 'worker'
        if handler_detail.device_user_id and handler_detail.device_chanel_id and handler_detail.device_type:
            if complain_array and deal_person_id:
                list_complain = str(complain_array).split(",")
                #deal_person_id = str(handler_array).split(",")
                for i in range(len(list_complain)):
                    com_id = int(list_complain[i])
                    complain = Complaints.objects.get(id=com_id)
                    complain.is_read = True
                    complain.is_worker_read = True
                    complain.status = 4
                    if user_obj:
                        complain.handler = user_obj
                    complain.save()
                    push_class = PushCheckClass(description, handler_detail, title, theme, role, complain,admin_profile,complain.id)
                    push_class.start()
                response_data = {'success': True, 'info': '授权成功并推送消息至处理人！'}
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:
            response_data = {'success': False, 'info': '请工作人员帮定手机端'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")



@transaction.atomic
@csrf_exempt
@login_required(login_url='/login/')
def worker_deal_complain(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        complain_array = request.POST.get("selected_complain_string", None)
        if complain_array:
            list_complain = str(complain_array).split(",")
            for i in range(len(list_complain)):
                re_id = int(list_complain[i])
                complain = Complaints.objects.get(id=re_id)
                complain.is_read = True
                complain.is_worker_read = True
                complain.status = 2
                user_obj = User.objects.get(username=complain.author)
                title = '消息通知'
                description = '你的投诉已经授权处理！'
                theme = 'complain'
                role = 'user'
                profile = ProfileDetail.objects.get(profile=user_obj)
                complain.save()
                if profile.device_user_id and profile.device_chanel_id and profile.device_type:
                    try:
                        push_class = ThreadClass(description, profile, title, theme, role)
                        push_class.start()
                    except Exception ,e:
                        print e
                        continue
            response_data = {'success': True, 'info': '工作人员处理中'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@transaction.atomic
@csrf_exempt
def complain_delete(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        complain_array = request.POST.get("selected_complain_string", None)
        if complain_array:
            list_complain_ = str(complain_array).split(",")
            for i in range(len(list_complain_)):
                com_id = int(list_complain_[i])
                Complaints.objects.get(id=com_id).delete()
            response_data = {'success': True, 'info': '删除成功'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")

@transaction.atomic
@csrf_exempt
def complain_complete(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        title="消息通知"
        description = '你的投诉已经完成处理！'
        theme = '投诉'
        role = 'user'
        complain_array = request.POST.get("selected_complain_string", None)
        if complain_array:
            list_complain_ = str(complain_array).split(",")
            for i in range(len(list_complain_)):
                com_id = int(list_complain_[i])
                complain = Complaints.objects.get(id=com_id)
                complain.status = 3
                complain.complete_time = datetime.datetime.now()
                complain.complete_date = datetime.datetime.now()
                complain.save()
                user_obj = User.objects.get(username=complain.author)
                profile = ProfileDetail.objects.get(profile=user_obj)
                push_class = ThreadClass(description, profile, title, theme, role)
                push_class.start()
                check_pleased = PleasedClass(complain,theme,complain.id)
                check_pleased.start()
            response_data = {'success': True, 'info': '提交成功！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@transaction.atomic
@csrf_exempt
def own_complain(request):
    start_time = request.POST.get('start_time', None)
    end_time = request.POST.get('end_time', None)
    if start_time and end_time:
        complains = Complaints.objects.filter(author=request.user.username, timestamp__range=[start_time, end_time])
    else:
        complains = Complaints.objects.filter(author=request.user.username).order_by('-timestamp')
    profile = ProfileDetail.objects.get(profile=request.user)
    wallet = Wallet.objects.filter(user_profile=profile)
    if wallet:
        wallet = wallet[0]
    if len(complains) > 0:
        paginator = Paginator(complains, 7)
        page = request.GET.get('page')
        try:
            complains_list = paginator.page(page)
        except PageNotAnInteger:
            complains_list = paginator.page(1)
        except EmptyPage:
            complains_list = paginator.page(paginator.num_pages)
        return render_to_response('own_complain.html', {
            'complains': complains_list,
            'user': request.user,
            'profile': profile,
            'change_community': 2,
            'show': True
        })
    return render_to_response('own_complain.html',
                              {'show': False, 'user': request.user, 'profile': profile, 'change_community': 2,'wallet': wallet})


@transaction.atomic
@csrf_exempt
@login_required
def complain_response(request):
    if request.method != u'POST':
        return redirect(index)
    else:
        complain_id = request.POST.get("complain_id", None)
        response_content = request.POST.get("response_content", None)
        selected_pleased = request.POST.get("selected_radio", None)
        profile = ProfileDetail.objects.get(profile=request.user)
        complain = Complaints.objects.get(id=complain_id)
        handler_profile = ProfileDetail.objects.get(profile=complain.handler)
        title = '消息通知'
        description = '用户已对你的处理作出评价！'
        theme = 'complain'
        theme_one = '投诉'
        role = 'worker'
        if complain:
            complain.pleased_reason = response_content
            complain.pleased = selected_pleased
            complain.save()
            push_thread = ThreadClass(description,handler_profile,title, theme, role)
            push_thread.start()
            judge_pleased = JudgeClass(complain.theme_one,handler_profile)
            judge_pleased.start()
            response_data = {'success': True, 'info': '评论成功！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:
            return render_to_response('own_complain.html', {'show': True, 'user': request.user, 'profile': profile})


@csrf_exempt
def show_image_detail(request, id):
    if request.method != u'GET':
        return redirect(index)
    else:
        type = request.GET.get("type", None)
        if type == 'complain':
            complain = Complaints.objects.get(id=id)
            if complain:
                return render_to_response('complain_img_detail.html', {
                    'complain': complain
                })
            else:
                return return_404_response()
        elif type == 'repair':
            repair = Repair.objects.get(id=id)
            if repair:
                return render_to_response('repair_img_detail.html', {
                    'repair': repair
                })
            else:
                return return_404_response()


@transaction.atomic
@csrf_exempt
def api_complain_create(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    else:
        complain_content = request.POST.get('content', None)
        complain_type = request.POST.get('category', None)
        profile = ProfileDetail.objects.get(profile=request.user)
        all_user_info = profile.community.profiledetail_set.all()
        community_admin = None
        for user_info in all_user_info:
            if user_info.profile.is_staff == True:
                community_admin = user_info
        upload__complain_src = request.FILES.get('upload_complain_img', None)
        #complain_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        complain_time = datetime.datetime.now()
        profile = ProfileDetail.objects.get(profile=request.user)
        if complain_content or complain_type:
            complain = Complaints(author=request.user.username)
            complain.content = complain_content
            complain.author_detail = profile
            complain.timestamp = complain_time
            complain.create_date = complain_time
            complain.type = complain_type
            complain.is_admin_read = True
            complain.community = profile.community
            if upload__complain_src:
                complain.src = upload__complain_src
            complain.save()
            check_admin = CheckAdminClass(complain,community_admin,'投诉',complain.id)
            check_admin.start()
            return HttpResponse(simplejson.dumps({'error': False, 'info': u'投诉创建成功'}), content_type='application/json')
        else:
            return HttpResponse(simplejson.dumps({'error': True, 'info': u'投诉创建失败'}), content_type='application/json')



@transaction.atomic
@csrf_exempt
def api_worker_deal_complain(request):
    if request.method != u'POST':
        return redirect(index)
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        complain_array = data.get("complains_id_string", None)
        if complain_array:
            list_complain = str(complain_array).split(",")
            for i in range(len(list_complain)):
                re_id = int(list_complain[i])
                complain = Complaints.objects.get(id=re_id)
                complain.is_read = True
                complain.is_worker_read = True
                complain.status = 2
                complain.save()
                user_obj = User.objects.get(username=complain.author)
                profile = ProfileDetail.objects.get(profile=user_obj)
                title = '消息通知'
                description = '你的投诉已经授权处理！'
                theme = 'complain'
                role = 'user'
                if profile.device_user_id and profile.device_chanel_id and profile.device_type:
                    try:
                        push_class = ThreadClass(description, profile, title, theme, role)
                        push_class.start()
                        #push_message(description, profile, title)
                    except Exception ,e:
                        print e
                        continue
            response_data = {'success': True, 'info': '已更改状态并发送消息至客户'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:
            response_data = {'success': False}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
    else:
            response_data = {'success': False}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@transaction.atomic
@csrf_exempt
def api_complain_response(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        complain_id = data.get("complain_id", None)
        response_content = data.get("response_content", None)
        selected_pleased = data.get("selected_pleased", None)
        complain = Complaints.objects.get(id=complain_id)
        handler_profile = ProfileDetail.objects.get(profile=complain.handler)
        title = '消息通知'
        description = '用户已对你的处理作出评价！'
        theme = '投诉'
        role = 'worker'
        if complain and selected_pleased:
            complain.pleased_reason = response_content
            complain.pleased = selected_pleased
            complain.save()
            push_thread = ThreadClass(description,handler_profile,title, theme, role)
            push_thread.start()
            judge_pleased = JudgeClass(complain.theme,handler_profile)
            judge_pleased.start()
            response_data = {'success': True, 'info': '反馈成功！'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
        else:
            response_data = {'success': False, 'info': '反馈失败！'}
            return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        return return_404_response()


@transaction.atomic
@csrf_exempt
def api_own_complain(request):
    convert_session_id_to_user(request)
    complains = Complaints.objects.filter(author=request.user.username).order_by('-timestamp')
    if len(complains) > 0:
        paginator = Paginator(complains, 20)
        page_count = paginator.num_pages
        page = request.GET.get('page')
        try:
            complains_list = paginator.page(page).object_list
        except PageNotAnInteger:
            complains_list = paginator.page(1)
        except EmptyPage:
            complains_list = paginator.page(paginator.num_pages)
        complain_list = list()
        local_time = None
        for complain_detail in complains_list:
            submit_time = complain_detail.timestamp
            local = submit_time.astimezone(UTC(8))
            complete_time = complain_detail.complete_time
            if complete_time:
                local_time = complete_time.astimezone(UTC(8))
            data = {
                'id': complain_detail.id,
                'complain_author': complain_detail.author,
                'author_community': complain_detail.community.title,
                'author_floor': complain_detail.author_detail.floor,
                'author_room': complain_detail.author_detail.gate_card,
                'content': complain_detail.content,
                'type': complain_detail.type,
                'deal_status': complain_detail.status,
                'pleased': complain_detail.pleased,
                'complete_time': str(local_time).split('.')[0],
                'src': complain_detail.src.name,
                'time': str(local).split('.')[0],
                'handler': str(complain_detail.handler)
            }
            complain_list.append(data)
        response_data = {'complain_list': complain_list, 'page_count': page_count, 'success': True}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        response_data = {'success': False}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


@transaction.atomic
@csrf_exempt
def api_complain_deal(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        admin_profile = ProfileDetail.objects.get(profile=request.user)
        data = simplejson.loads(request.body)
        complain_array = data.get("complains_id_string", None)
        deal_person_id = data.get("deal_person_id", None)
        title = '消息通知'
        description = '你有新的投诉需要处理'
        theme = 'complain'
        role = 'worker'
        user_obj = User.objects.get(id=deal_person_id)
        handler_detail = ProfileDetail.objects.get(profile=user_obj)
        if handler_detail.device_user_id and handler_detail.device_chanel_id and handler_detail.device_type:
            if complain_array and deal_person_id:
                list_complain_ = str(complain_array).split(",")
                for i in range(len(list_complain_)):
                    com_id = int(list_complain_[i])
                    complain = Complaints.objects.get(id=com_id)
                    complain.status = 4
                    complain.is_worker_read = True
                    complain.is_read = True
                    if user_obj:
                        complain.handler = user_obj
                    complain.save()
                    push_class = PushCheckClass(description, handler_detail, title, theme, role, complain,admin_profile,complain.id)
                    push_class.start()
                    #push_message(description, handler_detail, title)
                response_data = {'success': True, 'info': u'授权成功，并推送消息至处理人！'}
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
            else:
                response_data = {'success': False, 'info': u'请选择要处理的投诉'}
                return HttpResponse(simplejson.dumps(response_data), content_type="application/json")
        else:
            response_data = {'success': False, 'info': u'请工作人员绑定手机端'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@transaction.atomic
@csrf_exempt
def api_complain_complete(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    elif 'application/json' in request.META['CONTENT_TYPE'].split(';'):
        data = simplejson.loads(request.body)
        complain_array = data.get("complains_id_string", None)
        title = '消息通知'
        description = '你投诉已完成处理'
        theme = '投诉'
        role = 'user'
        if complain_array:
            list_complain_ = str(complain_array).split(",")
            for i in range(len(list_complain_)):
                com_id = int(list_complain_[i])
                complain = Complaints.objects.get(id=com_id)
                complain.status = 3
                complain.complete_time = datetime.datetime.now()
                complain.complete_date = datetime.datetime.now()
                user_obj = User.objects.get(username=complain.author)
                profile = ProfileDetail.objects.get(profile=user_obj)
                complain.save()
                push_class = ThreadClass(description, profile, title, theme, role)
                push_class.start()
                check_pleased = PleasedClass(complain,theme,complain.id)
                check_pleased.start()
            response_data = {'success': True, 'info': '提交成功！'}
            return HttpResponse(simplejson.dumps(response_data), content_type="application/json")


@transaction.atomic
@csrf_exempt
def api_show_all_complains(request):
    convert_session_id_to_user(request)
    community_id = request.GET.get("community_id", None)
    if community_id:
        community = Community.objects.get(id=community_id)
    else:
        response_data = {'info': '没有传入小区id', 'success': False}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    complains = Complaints.objects.filter(community=community).order_by('-timestamp')
    if len(complains) > 0:
        paginator = Paginator(complains, 20)
        page_count = paginator.num_pages
        page = request.GET.get('page')
        try:
            complains_list = paginator.page(page).object_list
        except PageNotAnInteger:
            complains_list = paginator.page(1)
        except EmptyPage:
            complains_list = paginator.page(paginator.num_pages)
        complain_list = list()
        local_time =None
        for complain_detail in complains_list:
            time = complain_detail.timestamp
            local = time.astimezone(UTC(8))
            complete_time = complain_detail.complete_time
            if complete_time:
                local_time = complete_time.astimezone(UTC(8))
            data = {
                'id': complain_detail.id,
                'complain_author': complain_detail.author,
                'author_community': complain_detail.community.title,
                'author_floor': complain_detail.author_detail.floor,
                'author_room': complain_detail.author_detail.gate_card,
                'content': complain_detail.content,
                'type': complain_detail.type,
                'complete_time':str(local_time).split('.')[0],
                'deal_status': complain_detail.status,
                'pleased': complain_detail.pleased,
                'src': complain_detail.src.name,
                'time': str(local).split('.')[0],
                'handler': str(complain_detail.handler)
            }
            complain_list.append(data)
        response_data = {'complains_list': complain_list, 'page_count': page_count, 'success': True}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        response_data = {'success': False, 'info': '该小区没有投诉'}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


@transaction.atomic
@csrf_exempt
def api_show_complains_by_status(request):
    convert_session_id_to_user(request)
    community_id = request.GET.get("community_id", None)
    complains_status = request.GET.get("status", None)
    profile = ProfileDetail.objects.get(profile=request.user)
    if community_id:
        community = Community.objects.get(id=community_id)
    else:
        response_data = {'info': '没有传入小区id', 'success': False}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    if request.user.is_staff:
            complains = Complaints.objects.filter(community=community, status=int(str(complains_status))).order_by('-timestamp')
    elif profile.is_admin:
        complains = Complaints.objects.filter(community=community, status=int(str(complains_status)), handler=request.user).order_by('-timestamp')
    else:
        complains = Complaints.objects.filter(community=community, status=int(str(complains_status)), author=request.user.username).order_by('-timestamp')
    if len(complains) > 0:
        paginator = Paginator(complains, 20)
        page_count = paginator.num_pages
        page = request.GET.get('page')
        try:
            complains_list = paginator.page(page).object_list
        except PageNotAnInteger:
            complains_list = paginator.page(1)
        except EmptyPage:
            complains_list = paginator.page(paginator.num_pages)
        complain_list = list()
        local_time = None
        for complain_detail in complains_list:
            time = complain_detail.timestamp
            local = time.astimezone(UTC(8))
            complete_time = complain_detail.complete_time
            if complete_time:
                local_time = complete_time.astimezone(UTC(8))
            data = {
                'id': complain_detail.id,
                'complain_author': complain_detail.author,
                'author_community': complain_detail.community.title,
                'author_floor': complain_detail.author_detail.floor,
                'author_room': complain_detail.author_detail.gate_card,
                'content': complain_detail.content,
                'complete_time':str(local_time).split('.')[0],
                'type': complain_detail.type,
                'deal_status': complain_detail.status,
                'pleased': complain_detail.pleased,
                'src': complain_detail.src.name,
                'time': str(local).split('.')[0],
                'handler': str(complain_detail.handler)
            }
            complain_list.append(data)
        response_data = {'complains_list': complain_list, 'page_count': page_count, 'success': True}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')
    else:
        response_data = {'success': False, 'info': '没有搜到要找的结果'}
        return HttpResponse(simplejson.dumps(response_data), content_type='application/json')


@transaction.atomic
@csrf_exempt
def api_complain_create_android(request):
    convert_session_id_to_user(request)
    if request.method != u'POST':
        return return_error_response()
    else:
        complain_content = unquote(str(request.POST.get('content', None)))
        complain_type = unquote(str(request.POST.get('category', None)))
        #upload__complain_src = unquote(str(request.FILES.get('upload_complain_img', None)))
        upload__complain_src = request.FILES.get('upload_complain_img', None)
        #complain_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        complain_time = datetime.datetime.now()
        profile = ProfileDetail.objects.get(profile=request.user)
        if complain_content or complain_type:
            complain = Complaints(author=request.user.username)
            complain.content = complain_content
            complain.timestamp = complain_time
            complain.author_detail = profile
            complain.type = complain_type
            complain.is_admin_read = True
            complain.community = profile.community
            if upload__complain_src:
                complain.src = upload__complain_src
            complain.save()
            return HttpResponse(simplejson.dumps({'error': False, 'info': u'投诉创建成功'}), content_type='application/json')
        else:
            return HttpResponse(simplejson.dumps({'error': True, 'info': u'投诉创建失败'}), content_type='application/json')
