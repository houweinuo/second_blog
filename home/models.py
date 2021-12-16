from django.db import models

# Create your models here.
from django.utils import timezone

# 定义文章分类
from users.models import User


class ArticleCategory(models.Model):
    # 栏目标题
    title = models.CharField(max_length=20, blank=True)
    # 创建时间
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'tb_category'
        verbose_name_plural = '类别管理'

    def __str__(self):
        return self.title


# 定义文章模型
class Article(models.Model):
    # 外键与User表关联， on_delete 删除时的操作  CASCADE级联操作（主从表一起删除）
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # 文章标题图
    avatar = models.ImageField(upload_to='article/%Y%m%d', blank=True)
    # 文章栏目的一对多
    category = models.ForeignKey(
        ArticleCategory,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='article',
    )
    # 文章标签
    tag = models.CharField(max_length=20, blank=True)
    # 标题
    title = models.CharField(max_length=20, blank=True, null=False)
    # 概要
    summary = models.CharField(max_length=200)
    # 内容
    content = models.TextField()
    # 浏览量(PositiveIntegerField必须是正整数)
    total_views = models.PositiveIntegerField(default=0)
    # 评论量
    comments_count = models.PositiveIntegerField(default=0)
    # 文章创建时间
    created = models.DateTimeField(default=timezone.now)
    # 文章更新时间
    updated = models.DateTimeField(auto_now=True)

    # 元数据
    class Meta:
        ordering = ('-created',)
        db_table = 'tb_article'
        verbose_name_plural = '文章管理'

    def __str__(self):
        return self.title


# 定义评论模型
class Comment(models.Model):
    # 评论内容
    content = models.TextField()
    # 评论文章
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True)
    # 发表评论的用户
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # 评论发布的时间
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.article.title

    class Meta:
        db_table = 'tb_comment'
        verbose_name_plural = '评论管理'
