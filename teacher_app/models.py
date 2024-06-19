from django.db import models


# Create your models here.
class Class(models.Model):
    name = models.CharField(verbose_name="班级名称", max_length=30)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, verbose_name="教师", null=True, blank=True)

    def __str__(self):
        return self.name

    def get_student_count(self):
        return self.students.count()


class Notification(models.Model):
    title = models.CharField(verbose_name="通知标题", max_length=255, null=True, blank=True)
    content = models.TextField(verbose_name="通知内容")
    date_posted = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    recipients = models.ManyToManyField(Class, verbose_name="接收班级")

    def __str__(self):
        return self.content[:50]


class Teacher(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=6)
    userid = models.CharField(verbose_name="教工号", max_length=10)
    password = models.CharField(verbose_name="密码", max_length=128)
    email = models.EmailField(verbose_name="邮箱", unique=True, null=True, blank=True)
    phone_num = models.CharField(verbose_name="电话号码", max_length=12, null=True)
    last_login = models.DateTimeField(verbose_name='登录时间', null=True, blank=True)


class Exercise(models.Model):
    title = models.CharField(verbose_name="练习标题", max_length=255)
    content = models.TextField(verbose_name="练习描述")
    published_at = models.DateTimeField(verbose_name="发布时间", auto_now_add=True)
    deadline = models.DateTimeField(verbose_name="截止时间")

    teacher = models.ForeignKey(Teacher, verbose_name="发布教师", on_delete=models.SET_NULL, null=True)
    classes = models.ManyToManyField(Class, verbose_name="参与练习的班级", blank=True)

    def __str__(self):
        return self.title


class ExerciseQuestion(models.Model):
    exercise = models.ForeignKey(Exercise, verbose_name="练习", on_delete=models.CASCADE,
                                 related_name='questions', null=True)
    title = models.CharField(max_length=200, verbose_name="题目标题", null=True, blank=True)
    content = models.TextField(verbose_name="题目内容")
    memory_limit = models.IntegerField(verbose_name="内存限制", default=0)
    time_limit = models.IntegerField(verbose_name="时间限制", default=0)
    answer = models.TextField(verbose_name="答案", null=True, blank=True)

    def __str__(self):
        return f"{self.exercise.title} - {self.content}"


class ExerciseQuestionTestCase(models.Model):
    question = models.ForeignKey(ExerciseQuestion, verbose_name="题目", on_delete=models.CASCADE,
                                 related_name='exercise_testcases')
    input = models.TextField(verbose_name="测试输入")
    expected_output = models.TextField(verbose_name="预期输出")

    def __str__(self):
        return f"{self.question.title} - {self.question.content}"


class Exam(models.Model):
    title = models.CharField(verbose_name="考试标题", max_length=255)
    content = models.TextField(verbose_name="考试描述")
    published_at = models.DateTimeField(verbose_name="发布时间", auto_now_add=True)
    deadline = models.DateTimeField(verbose_name="截止时间")

    teacher = models.ForeignKey(Teacher, verbose_name="发布教师", on_delete=models.SET_NULL, null=True)
    classes = models.ManyToManyField(Class, verbose_name="参与考试的班级", blank=True)

    def __str__(self):
        return self.title


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, verbose_name="考试", on_delete=models.CASCADE,
                             related_name='questions', null=True)
    title = models.CharField(max_length=200, verbose_name="题目标题", null=True, blank=True)
    content = models.TextField(verbose_name="题目内容")
    memory_limit = models.IntegerField(verbose_name="内存限制", default=0)
    time_limit = models.IntegerField(verbose_name="时间限制", default=0)
    answer = models.TextField(verbose_name="答案", null=True, blank=True)

    def __str__(self):
        return f"{self.exam.title} - {self.content}"


class ExamQuestionTestCase(models.Model):
    question = models.ForeignKey(ExamQuestion, verbose_name="题目", on_delete=models.CASCADE,
                                 related_name='exam_testcases')
    input = models.TextField(verbose_name="测试输入")
    expected_output = models.TextField(verbose_name="预期输出")

    def __str__(self):
        return f"{self.question.title} - {self.question.content}"


class ReportScore(models.Model):
    teacher = models.ForeignKey(Teacher, verbose_name="教师", on_delete=models.CASCADE, related_name='report_scores')
    totalscore = models.IntegerField(verbose_name="总分")
    contents = models.IntegerField(verbose_name="内容得分")
    firstrow = models.IntegerField(verbose_name="首行得分")
    fontsize = models.IntegerField(verbose_name="字体大小得分")
    image = models.IntegerField(verbose_name="图片得分")
    pagenum = models.IntegerField(verbose_name="页数得分")

    def __str__(self):
        return f"{self.teacher.name} - 报告评分"
