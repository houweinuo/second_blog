from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

# 继承AbstractUser类
class User(AbstractUser):
    # unique 设置手机号为唯一字段
    mobile = models.CharField(max_length=20, unique=True, blank=True)
    # 个人简介
    users_desc = models.TextField(max_length=500, blank=True)
    # 头像  upload_to  存储位置
    avatar = models.ImageField(blank=True, upload_to='avatar/%Y%m%d/')
    # 修改认证字段为mobile
    USERNAME_FIELD = 'mobile'
    # 创建超级管理员需要输入的字段
    REQUIRED_FIELDS = ['username', 'email']

    # # 内部类 class Meta 用于给 model 定义元数据  Meta类中不需要加  "，"逗号
    class Meta:
        db_table = 'tb_user'
        # admin后台显示
        verbose_name_plural = '用户信息'

    def __str__(self):
        # 后台显示字段
        return self.mobile
    """
    模型定义完成要进行模型迁移
    python manage.py makemigrations
    python manage.py migrate
    """
