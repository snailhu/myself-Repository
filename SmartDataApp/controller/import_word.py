#coding:utf-8
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
import HTMLParser
from django.views.decorators.csrf import csrf_exempt
from SmartDataApp.models import Community, Notification, ProfileDetail
import datetime
import os
from shutil import copyfile
import simplejson
from docx2html import convert

@transaction.atomic
@csrf_exempt
def import_notification(request):
        file_name = request.FILES.get('Filedata')
        if str(file_name).split(".")[1]!='docx':
            return HttpResponse(simplejson.dumps({'error': True}), content_type='application/json')
        else:
            WriteFileData = open('./static/notification.docx', 'wb')
            WriteFileData.write(file_name.read())
            WriteFileData.close()
            html = convert('./static/notification.docx',image_handler=handle_image)
            profile=ProfileDetail.objects.get(profile=request.user)
            community = Community.objects.get(id=profile.community.id)
            html_parser= HTMLParser.HTMLParser()
            notification = Notification()
            notification.notification_community = community
            notification.notification_content =html_parser.unescape(html).replace("\"","\\\"")
            notification.notification_theme =str(file_name).split(".")[0]
            notification.notification_time = datetime.datetime.now()
            notification.save()
            WriteFileData.close()
            return HttpResponse(simplejson.dumps({'success': True}), content_type='application/json')

def handle_image(image_id, relationship_dict):
     image_path = relationship_dict[image_id]
     # Now do something to the image. Let's move it somewhere.
     _, filename = os.path.split(image_path)
     destination_path = os.path.join('./static/word/', filename)
     copyfile(image_path, destination_path)
     # Return the `src` attribute to be used in the img tag
     return '%s' %'/static/word/'+filename