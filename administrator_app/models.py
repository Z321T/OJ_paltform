from django.db import models

from consumer.models import CustomUser


# Create your models here.
class Administrator(CustomUser):
    name = models.CharField(verbose_name="姓名", max_length=6)
    phone_num = models.CharField(verbose_name="电话号码", max_length=12, null=True)


class AdminNotification(models.Model):
    administrator = models.ForeignKey(Administrator, on_delete=models.CASCADE, related_name='notifications',
                                      verbose_name="课程负责人", null=True, blank=True)
    title = models.CharField(verbose_name="通知标题", max_length=255, null=True, blank=True)
    content = models.TextField(verbose_name="通知内容")
    date_posted = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")


class ProgrammingExercise(models.Model):
    title = models.CharField(verbose_name="题目标题", max_length=255)
    description = models.TextField(verbose_name="题目描述")
    posted_by = models.ForeignKey(Administrator, verbose_name="发布教师", on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    deadline = models.DateTimeField(verbose_name="截止时间")

    def __str__(self):
        return self.title


class AdminExam(models.Model):
    title = models.CharField(verbose_name="考试标题", max_length=255)
    content = models.TextField(verbose_name="考试描述")
    starttime = models.DateTimeField(verbose_name="开始时间")
    deadline = models.DateTimeField(verbose_name="截止时间")

    teacher = models.ForeignKey(Administrator, verbose_name="发布教师", on_delete=models.CASCADE, null=True)
    classes = models.ManyToManyField('teacher_app.Class', verbose_name="参与考试的班级", blank=True)

    def __str__(self):
        return self.title


class AdminExamQuestion(models.Model):
    exam = models.ForeignKey(AdminExam, verbose_name="考试", on_delete=models.CASCADE,
                             related_name='questions', null=True)
    title = models.CharField(max_length=200, verbose_name="题目标题", null=True, blank=True)
    content = models.TextField(verbose_name="题目内容")
    memory_limit = models.IntegerField(verbose_name="内存限制", default=0)
    time_limit = models.IntegerField(verbose_name="时间限制", default=0)

    def __str__(self):
        return f"{self.exam.title} - {self.content}"


class AdminExamQuestionTestCase(models.Model):
    question = models.ForeignKey(AdminExamQuestion, verbose_name="题目", on_delete=models.CASCADE,
                                 related_name='adminexam_testcases')
    input = models.TextField(verbose_name="测试输入")
    expected_output = models.TextField(verbose_name="预期输出")

    def __str__(self):
        return f"{self.question.title} - {self.question.content}"
