import re
from random import randint

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django.db import DatabaseError
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from home.models import ArticleCategory, Article, Comment
from libs.captcha.captcha import captcha
# 导入redis连接库
from django_redis import get_redis_connection
# 导入日志
import logging

# 创建日志对象
from libs.yunliantong.SendMessage import send_message
from users.models import User

logger = logging.getLogger('django')

# Create your views here.

# 定义用户注册视图


# 注册界面视图
from utils.response_code import RETCODE


class RegisterView(View):
    # get请求转到这里  每个请求需要接收request
    def get(self, request):
        """

        :param request: 请求对象
        :return:注册 register界面
        """
        return render(request, 'register.html')

    def post(self, request):
        # 获取参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('缺少必要参数')
        if password != password2:
            return HttpResponseBadRequest('密码输入不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('请输入正确的手机号')
        if not re.match(r'^[a-zA-Z0-9]{8,20}', password):
            return HttpResponseBadRequest('请输入8-20位的密码')
        # 验证短信验证码
        redis_conn = get_redis_connection()
        sms_code_server = redis_conn.get(f'sms:{mobile}')
        if sms_code_server is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if sms_code_server.decode() != sms_code:
            return HttpResponseBadRequest('短信验证码错误')
        # 保存注册数据
        try:
            user = User.objects.create_user(mobile=mobile, password=password, username=mobile)
            # 实现状态保持
            login(request, user)
        except DatabaseError:
            return HttpResponseBadRequest('注册失败')
        response = redirect(reverse('home:index'))
        # 设置cookie
        response.set_cookie('is_login', True)
        # 设置用户名有效时间
        response.set_cookie('username', user.username, max_age=30 * 24 * 3600)
        return response


# 图形验证码后端视图
class ImageCodeView(View):
    def get(self, request):
        # 获取uuid
        uuid = request.GET.get('uuid')
        # 判断uuid是否为None
        if uuid is None:
            return HttpResponseBadRequest('请求参数错误')
        # 获取验证码内容
        text, image = captcha.generate_captcha()
        #         将图片验证码内容保存到redis中
        redis_conn = get_redis_connection('default')
        redis_conn.setex(f'img:{uuid}', 300, text)
        # 返回响应
        return HttpResponse(image, content_type='image/jpeg')


# 短信验证码视图
class SmsCodeView(View):
    def get(self, request):
        # 接收参数
        img_code_client = request.GET.get('image_code')
        mobile = request.GET.get('mobile')
        uuid = request.GET.get('uuid')
        # 校验参数
        if not all([img_code_client, mobile, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必要参数'})
        # 创建连接到数据库的对象
        redis_conn = get_redis_connection('default')
        # 提取图片验证码
        img_code_server = redis_conn.get(f'img:{uuid}')
        if img_code_server is None:
            # 图片验证码不存在或者失效
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码失效'})
        # 删除验证码
        try:
            redis_conn.delete(f'img:{uuid}')
        except Exception as e:
            logger.error(e)
        # 对比图片验证码
        img_code_server = img_code_server.decode()
        logger.info(img_code_server)
        if img_code_server.lower() != img_code_client.lower():
            return JsonResponse({'code': RETCODE.SMSCODERR, 'errmsg': '图片验证码错误'})

        # 生成短信验证码：生成6位数验证码
        sms_code = '%06d' % randint(0, 999999)
        # 将验证码输出在控制台，以方便调试
        logger.info(sms_code)
        # 保存短信验证码到redis中，并设置过期时间
        redis_conn.setex(f'sms:{mobile}', 300, sms_code)
        # 发送短信验证码
        send_message(1, mobile, [sms_code, 5])
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})


# 登录界面视图
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        if not all([mobile, password]):
            return HttpResponseBadRequest('登录所需参数不全')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式输入不正确')
        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码为8-20位')
        # 认证登录字段
        user = authenticate(mobile=mobile, password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')
        login(request, user)
        next = request.POST.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('home:index'))

        if remember != 'on':
            # 如果没有记住用户，浏览器会话结束就过期
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, 24 * 3600 * 30)
        else:
            # None表示两周
            request.session.set_expiry(None)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, 24 * 3600 * 30)
        return response


# 退出登录 删除cookie标识
class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        return response


# 忘记密码视图
class ForgetPasswordView(View):
    def get(self, request):
        return render(request, 'forget_password.html')

    def post(self, request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('参数不全')
        if re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式输入不正确')
        if re.match(r'[0-9a-zA-Z]{8,20}', password):
            return HttpResponseBadRequest('请输入8-20位的密码')
        if password != password2:
            return HttpResponseBadRequest('两次密码输入不一致')
        # 验证短信验证码
        redis_conn = get_redis_connection('default')
        sms_code_server = redis_conn.get(f'sms:{mobile}')
        if sms_code_server is None:
            return HttpResponseBadRequest('短信验证码不存在或已过期')
        if sms_code_server != sms_code:
            return HttpResponseBadRequest('短信验证码不正确')
        # 根据手机号查询数据
        try:
            user = User.objects.get('mobile')
        except User.DoesNotExist:
            try:
                User.objects.create_user(username=mobile, mobile=mobile, password=password)
            except Exception:
                return HttpResponseBadRequest('修改失败， 请稍后再次尝试')
        # 如果查询到手机号，则更改密码
        else:
            user.set_password(password)
            user.save()
        return redirect(reverse('users:login'))


# 用户中心展示

class UserCenterView(LoginRequiredMixin, View):
    # @login_required
    def get(self, request):
        user = request.user
        username = user.username
        mobile = user.mobile
        if user.avatar:
            avatar = user.avatar.url
        else:
            avatar = None
        user_desc = user.users_desc
        print(username, mobile, user_desc)
        return render(request, 'center.html', locals())

    # 用户中心修改
    def post(self, request):
        user = request.user
        # 如果没有传递过来参数，仍然用原来的
        username = request.POST.get('username', user.username)
        avatar = request.FILES.get('avatar')
        desc = request.POST.get('desc', user.users_desc)
        # 修改数据库信息
        try:
            user.username = username
            user.users_desc = desc

            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('更新失败，请稍后重试')
        # 返回响应, 刷新页面
        response = redirect(reverse('users:center'))
        # 因为更改了username 所以更新cookie
        response.set_cookie('username', user.username, max_age=30 * 24 * 3600)
        return response


# 写博客页面视图
class WriteBlogView(LoginRequiredMixin, View):
    def get(self, request):
        categories = ArticleCategory.objects.all()
        return render(request, 'write_blog.html', locals())

    def post(self, request):
        title = request.POST.get('title')
        avatar = request.FILES.get('avatar')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        user = request.user
        # 判断文章分类信息是否存在
        try:
            article_category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类噢')
        # 保存数据库
        try:
            article = Article.objects.create(
                author=user,
                avatar=avatar,
                title=title,
                summary=summary,
                tag=tags,
                content=content,
                category=article_category,
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败， 请稍后重试')
        # 返回响应
        return redirect(reverse('home:index'))



