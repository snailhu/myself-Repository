#coding:utf-8
from django.db import transaction
from SmartDataApp.models import Housekeeping_items, Repair_item
from xlrd import open_workbook
from django.http import HttpResponse

from django.shortcuts import render, render_to_response
from django.views.decorators.csrf import csrf_exempt
import simplejson

@transaction.atomic
@csrf_exempt
def import_housekeeping_item(request):
        file_name = request.FILES.get('Filedata')
        last_name = file_name.name.split('.')[-1]
        #WriteFileData = open('./static/housekeeping_excel.'+str(last_name)+'', 'wb')
        WriteFileData = open('./static/housekeeping_excel.xls', 'wb')
        WriteFileData.write(file_name.read());
        WriteFileData.close()
        #book = open_workbook('./static/housekeeping_excel.'+str(last_name)+'', on_demand=True)
        book = open_workbook('./static/housekeeping_excel.xls', on_demand=True)
        for name in book.sheet_names():
            if name.endswith('1'):
                sheet = book.sheet_by_name(name)
                cells = sheet._cell_values
                for cell in cells:
                    if type(cell[0]) is float:
                        house_item = Housekeeping_items.objects.filter(item=cell[1].encode('utf8'))
                        if house_item:
                            house_item[0].content = cell[2].encode('utf8')
                            house_item[0].price_description = cell[3].encode('utf8')
                            house_item[0].remarks = cell[4].encode('utf8')
                            #print table.cell(row_index,col_index).value
                            house_item[0].save()
                        else:

                            house_item = Housekeeping_items()
                            house_item.item = cell[1].encode('utf8')
                            house_item.content = cell[2].encode('utf8')
                            house_item.price_description = cell[3].encode('utf8')
                            house_item.remarks = cell[4].encode('utf8')
                            #print table.cell(row_index,col_index).value
                            house_item.save()
        return HttpResponse(simplejson.dumps({'success': True}), content_type='application/json')

@transaction.atomic
@csrf_exempt
def import_repair_item(request):
        file_name = request.FILES.get('Filedata')
        WriteFileData = open('./static/repair_excel.xls', 'wb')
        WriteFileData.write(file_name.read())
        WriteFileData.close()
        book = open_workbook('./static/repair_excel.xls', on_demand=True)
        for name in book.sheet_names():
            if name.endswith('1'):
                sheet = book.sheet_by_name(name)
                cells = sheet._cell_values
                for cell in cells:
                    if type(cell[0]) is float:
                        repair_item = Repair_item.objects.filter(item=cell[1].encode('utf8'))
                        if repair_item:
                            repair_item[0].price = cell[2].encode('utf8')
                            #print table.cell(row_index,col_index).value
                            repair_item[0].save()
                        else:
                            repair_item = Repair_item()
                            repair_item.type = cell[1].encode('utf8')
                            repair_item.item = cell[2].encode('utf8')
                            repair_item.price = cell[3]
                            repair_item.save()
        return HttpResponse(simplejson.dumps({'success': True}), content_type='application/json')

def ycjmb_test():
    book = open_workbook(u'有偿价目表.xls', on_demand=True)
    for name in book.sheet_names():
        if name.endswith('1'):
            sheet = book.sheet_by_name(name)
            cells = sheet._cell_values
            for cell in cells:
                if type(cell[0]) is float:
                    print '{} {} {}'.format(str(cell[0]).encode('utf8'), cell[1].encode('utf8'),
                                            cell[2] if type(cell[2]) is float else cell[2].encode('utf8'))
            print


def jzwfbj_test():
    book = open_workbook(u'家政服务报价样式表.xls', on_demand=True)
    for name in book.sheet_names():
        if name.endswith('1'):
            sheet = book.sheet_by_name(name)
            cells = sheet._cell_values
            for cell in cells:
                if type(cell[0]) is float:
                    print '{} {} {} {} {}'.format(str(cell[0]).encode('utf8'), cell[1].encode('utf8'), cell[2].encode('utf8'),
                                            cell[3].encode('utf8'), cell[4].encode('utf8'))
            print

#
#if __name__ == '__main__':
#    ycjmb_test()
#    jzwfbj_test()