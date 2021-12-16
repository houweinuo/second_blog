# -*- coding: utf-8 -*-
# @Time    : 2021/11/7 19:41
# @Author  : HWN
# @File    : urls.py
# @Software: PyCharm
from django.urls import path

from home.views import IndexView, DetailView, ExceptView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('detail/', DetailView.as_view(), name='detail'),
    path('404/', ExceptView.as_view())
]
