#coding:utf-8
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Community(models.Model):
    title = models.CharField(max_length=50, null=False, unique=True, blank=False)
    description = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.title


class Picture(models.Model):
    author = models.ForeignKey(User, null=True)
    title = models.CharField(max_length=100, null=False, unique=True, blank=False)
    comment = models.CharField(max_length=255, null=True)
    src = models.ImageField(upload_to='uploads/%Y/%m/%d', null=True)
    timestamp_add = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)
    like = models.IntegerField(default=0)
    keep = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class ProfileDetail(models.Model):
    profile = models.OneToOneField(User)
    avatar = models.ImageField(upload_to='avatar/%Y/%m/%d')
    phone_number = models.CharField(max_length=11, null=True)
    community = models.ForeignKey(Community, null=True)
    #pictures = models.ManyToManyField(Picture, null=True)
    floor = models.CharField(max_length=20, null=True)
    gate_card = models.CharField(max_length=20, null=True)
    address = models.CharField(max_length=100, null=True)
    is_admin = models.BooleanField(default=False)
    house_acreage = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    device_user_id = models.CharField(max_length=250, null=True, default=0)
    device_chanel_id = models.CharField(max_length=250, null=True, default='')
    device_type = models.CharField(max_length=250, null=True, default='')


    def __str__(self):
        return self.phone_number


class Complaints(models.Model):
    content = models.CharField(max_length=1000, null=True, blank=True, default='')
    author = models.CharField(blank=True, null=True, max_length=250, default='')
    timestamp = models.DateTimeField(null=True)
    create_date = models.DateField(null=True)
    handler = models.ForeignKey(User, null=True)
    pleased = models.IntegerField(default=0)
    type = models.CharField(max_length=200)
    status = models.IntegerField(default=1)
    src = models.ImageField(upload_to='uploads/%Y/%m/%d', null=True)
    pleased_reason = models.CharField(max_length=250, null=True)
    community = models.ForeignKey(Community, null=True)
    is_read = models.BooleanField(default=False)
    is_worker_read = models.BooleanField(default=False)
    is_admin_read = models.BooleanField(default=False)
    author_detail = models.ForeignKey(ProfileDetail, null=True)
    complete_time = models.DateTimeField(null=True)
    complete_date = models.DateField(null=True)

    def __str__(self):
        return self.content


class Repair(models.Model):
    content = models.CharField(max_length=250, null=True, blank=True, default='')
    author = models.CharField(blank=True, null=True, max_length=250, default='')
    timestamp = models.DateTimeField(default=timezone.now)
    create_date = models.DateField(null=True)
    handler = models.ForeignKey(User, null=True)
    pleased = models.IntegerField(default=0)
    type = models.CharField(max_length=200)
    status = models.IntegerField(default=1)
    src = models.ImageField(upload_to='uploads/%Y/%m/%d', null=True)
    pleased_reason = models.CharField(max_length=250, null=True)
    repair_item = models.CharField(max_length=200, default='')
    price = models.IntegerField(default=0)
    community = models.ForeignKey(Community, null=True)
    is_read = models.BooleanField(default=False)
    is_worker_read = models.BooleanField(default=False)
    is_admin_read = models.BooleanField(default=False)
    author_detail = models.ForeignKey(ProfileDetail, null=True)
    complete_time = models.DateTimeField(null=True)
    complete_date = models.DateField(null=True)

    def __str__(self):
        return self.content


class Express(models.Model):
    author = models.ForeignKey(ProfileDetail, null=True)
    arrive_time = models.DateTimeField(default=timezone.now)
    arrive_date = models.DateField(null=True)
    submit_get_date = models.DateField(null=True)
    get_time = models.DateTimeField(null=True)
    type = models.CharField(max_length=200)
    status = models.BooleanField(default=False)
    handler = models.ForeignKey(User, null=True)
    pleased_reason = models.CharField(max_length=250, null=True)
    pleased = models.IntegerField(default=0)
    allowable_get_express_time = models.CharField(max_length=200, default='')
    community = models.ForeignKey(Community, null=True)
    is_read = models.BooleanField(default=False)
    is_worker_read = models.BooleanField(default=False)
    is_admin_read = models.BooleanField(default=False)
    submit_express_status = models.IntegerField(default=0)
    signer = models.CharField(max_length=250, null=True, blank=True)
    complete_time = models.DateTimeField(null=True)
    complete_date = models.DateField(null=True)

    def __str__(self):
        return self.type


class Repair_item(models.Model):
    item = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    price = models.IntegerField(default=0)
    community = models.ForeignKey(Community, null=True)

    def __str__(self):
        return self.type


class Housekeeping_items(models.Model):
    item = models.CharField(max_length=250, null=True)
    content = models.CharField(max_length=250, null=True)
    price = models.IntegerField(default=0, null=True)
    remarks = models.CharField(max_length=250, null=True)
    price_description = models.CharField(max_length=250, null=True)
    community = models.ForeignKey(Community, null=True)

    def __str__(self):
        return self.content


class Housekeeping(models.Model):
    author = models.ForeignKey(ProfileDetail, null=True)
    housekeeping_item = models.ForeignKey(Housekeeping_items, null=True)
    time = models.DateTimeField(null=True)
    apply_date = models.DateField(null=True)
    status = models.IntegerField(default=1)
    pleased = models.IntegerField(default=0)
    pleased_reason = models.CharField(max_length=250, null=True)
    handler = models.ForeignKey(User, null=True)
    community = models.ForeignKey(Community, null=True)
    is_read = models.BooleanField(default=False)
    is_worker_read = models.BooleanField(default=False)
    is_admin_read = models.BooleanField(default=False)
    allow_deal_time = models.CharField(max_length=250, null=True)

    def __str__(self):
        return self.author


class Wallet(models.Model):
    user_profile = models.OneToOneField(ProfileDetail, null=True)
    money_sum = models.DecimalField(max_digits=19, decimal_places=6, default=0.0)
    grade_sum = models.IntegerField(default=0)

    def __str__(self):
        return self.money_sum


class Transaction(models.Model):
    action = models.CharField(max_length=250, null=True)
    time = models.DateTimeField(null=True)
    order_number = models.CharField(max_length=250, null=True)
    money_num = models.DecimalField(max_digits=19, decimal_places=6, default=0.0)
    grade_num = models.IntegerField(default=0)
    remark = models.CharField(max_length=250, null=True)
    wallet_profile = models.ForeignKey(Wallet, null=True)

    def __str__(self):
        return self.action


class Notification(models.Model):
    notification_content = models.CharField(max_length=100000, blank=True, null=True)
    notification_time = models.DateTimeField(null=True)
    notification_theme = models.CharField(max_length=250, blank=True, null=True)
    notification_community = models.ForeignKey(Community, null=True)

    def __str__(self):
        return self.notification_content


class Park_fee(models.Model):
    author = models.ForeignKey(ProfileDetail, null=True)
    pay_type = models.CharField(max_length=250, null=True)
    park_type = models.CharField(max_length=250, null=True)
    renewal_fees = models.IntegerField(default=0)
    car_number = models.CharField(max_length=250, null=True)
    valid_time = models.DateTimeField(default=timezone.now, null=True)
    deadline = models.DateField(null=True)
    send_message =  models.IntegerField(default=0)
    position_num = models.IntegerField(default=0)
    order_number = models.IntegerField(max_length=10, null=True)
    pay_date = models.DateField(null=True)
    pay_status=models.IntegerField(default=0)

    def __str__(self):
        return self.car_number

class Property_fee(models.Model):
    author = models.ForeignKey(ProfileDetail, null=True)
    type = models.CharField(max_length=250, null=True)
    pay_status = models.IntegerField(default=0)
    valid_time = models.DateTimeField(default=timezone.now, null=True)
    deadline = models.DateField(null=True)
    remind_date = models.DateField(null=True)
    send_message = models.IntegerField(default=0)
    send_remind_message = models.IntegerField(default=0)
    pay_date = models.DateField(null=True)

    def __str__(self):
        return self.car_number

class Fees(models.Model):
    name = models.CharField(max_length=250, null=True)
    type = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=19, decimal_places=3, default=0.0)

    def __str__(self):
        return self.name


class ChinaPayHistory(models.Model):
    version = models.CharField(max_length=250, null=True, default=u'1.0.0')
    charset = models.CharField(max_length=250, null=True, default=u'UTF-8')
    sign_method = models.CharField(max_length=250, null=True, default=u'MD5')
    signature = models.CharField(max_length=250, null=True)
    trance_type = models.CharField(max_length=250, null=True, default=u'01')
    resp_code = models.CharField(max_length=250, null=True, default='00')
    resp_msg = models.CharField(max_length=250, null=True)
    mer_abbr = models.CharField(max_length=250, null=True)
    mer_id = models.CharField(max_length=250, null=True)
    order_number = models.CharField(max_length=250, null=True)
    trance_number = models.CharField(max_length=250, null=True)
    trace_time = models.CharField(max_length=100, null=True)
    qid = models.CharField(max_length=300, null=True)
    order_currency = models.CharField(max_length=250, null=True, default=u'156')
    order_amount = models.CharField(max_length=250, null=True)
    resp_time = models.CharField(max_length=250, null=True)
    settle_amount = models.CharField(max_length=250, null=True)
    settle_currency = models.CharField(max_length=250, null=True)
    settle_date = models.CharField(max_length=250, null=True)
    exchange_rate = models.CharField(max_length=250, null=True)
    exchange_date = models.CharField(max_length=250, null=True)
    cup_reserved = models.CharField(max_length=250, null=True)
    user = models.ForeignKey(User, null=True)

    def __str__(self):
        return self.signature


class OrderNumber(models.Model):
    number = models.CharField(max_length=10, null=True, default=u'10000000')

class Car_Washing(models.Model):
    author = models.ForeignKey(ProfileDetail, null=True)
    apply_time = models.DateTimeField(default=timezone.now)
    start_time = models.DateTimeField(default=timezone.now)
    washing_type = models.CharField(max_length=50)
    washing_case = models.CharField(max_length=50)
    other_car_num = models.CharField(max_length=10)
    washing_status = models.IntegerField(default=0)
    order_number = models.CharField(max_length=10, null=True)
    pay_date=models.DateTimeField(null=True)
    pay_status=models.IntegerField(default=0)
    def __str__(self):
        return self.author

class Fee_standard(models.Model):
    type = models.CharField(max_length=250, null=True)
    deadline = models.DateField(null=True,default=0)
    fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    def __str__(self):
        return self.type


