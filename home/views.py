from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from home.models import ArticleCategory, Article, Comment
from django.http import HttpResponseNotFound, HttpResponse


class IndexView(View):
    def get(self, request):
        # 默认为1 1 10
        cat_id = request.GET.get('cat_id', 1)
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)

        # 判断分类id
        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')
        # 获取博客分类信息
        categories = ArticleCategory.objects.all()
        # 分页数据
        articles = Article.objects.filter(category=category)
        # 创建分页器
        paginator = Paginator(articles, page_size)
        # 获取每一页的商品数据
        try:
            page_articles = paginator.get_page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')
        # 获取总页数
        total_page = paginator.num_pages

        return render(request, 'index.html', locals())


# 文章详情页面的展示
class DetailView(View):
    def get(self, request):
        id = request.GET.get('id')
        categories = ArticleCategory.objects.all()
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return redirect(reverse('home:404'))
        # 增加文章浏览量
        else:
            article.total_views += 1
            article.save()
        category = article.category
        # 推荐文章 增加热点数据
        hot_articles = Article.objects.order_by('-total_views')[:9]

        return render(request, 'detail.html', locals())


class ExceptView(View):
    def get(self, request):
        return render(request, '404.html')


class DetailView(View):
    def get(self, request):
        id = request.GET.get('id')
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 5)
        # 获取博客分类信息
        categories = ArticleCategory.objects.all()
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return HttpResponseNotFound('没有此文章')
        else:
            article.total_views += 1
            article.save()
        hot_article = Article.objects.order_by('-total_views')[:9]
        comments = Comment.objects.filter(article=article).order_by('-created')[:9]
        # 创建分页器
        paginator = Paginator(comments, page_size)
        try:
            page_comments = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')
        total_count = comments.count()

        # 获取总页数
        total_page = paginator.num_pages
        category = article.category
        return render(request, 'detail.html', locals())

    def post(self, request):
        user = request.user
        # 判断用户是否登录
        if user and user.is_authenticated:
            id = request.POST.get('id')
            content = request.POST.get('content')
            # 判断文章是否存在
            try:
                article = Article.objects.get(id=id)
            except Article.DoesNotExist:
                return HttpResponseNotFound('没有此文章')
            # 保存
            Comment.objects.create(
                content=content,
                article=article,
                user=user,
            )
            article.comments_count += 1
            article.save()
            path = reverse('home:detail') + '?id={}'.format(article.id)
            return redirect(path)
        else:
            return redirect(reverse('users:login'))
