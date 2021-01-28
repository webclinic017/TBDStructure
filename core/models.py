from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class User(AbstractUser):
    username = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return "{}".format(self.email)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    zip = models.CharField(max_length=5, blank=True, null=True)


class MonitorStock(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='monitorstock')
    strategy = models.CharField(max_length=100)
    date = models.CharField(max_length=20)
    codelist = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {} {}'.format(self.user.username, self.strategy, self.date)


class PortHistory(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='history')
    strategy = models.CharField(max_length=100)
    date = models.CharField(max_length=20)
    traded_stock = models.CharField(max_length=20)
    traded_time = models.CharField(max_length=20)
    action = models.CharField(max_length=10) # 1: buy, 0: sell
    amount = models.IntegerField()
    price = models.IntegerField()

    def __str__(self):
        return f'{self.user.username} {self.date} {self.strategy} {self.trade_stock}'