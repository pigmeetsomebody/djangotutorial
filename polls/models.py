from django.db import models
from django.utils import timezone

class Question(models.Model):
    question_text = models.CharField(max_length=200, verbose_name='问题描述')
    pub_date = models.DateTimeField('发布时间', default=timezone.now)

    def __str__(self):
        return self.question_text
    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    class Meta:
        verbose_name = '问题'
        verbose_name_plural = '问题'

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='所属问题')
    choice_text = models.CharField(max_length=200, verbose_name='选项描述')
    votes = models.IntegerField(default=0, verbose_name='得票数')

    def __str__(self):
        return self.choice_text

    class Meta:
        verbose_name = '选项'
        verbose_name_plural = '选项'
