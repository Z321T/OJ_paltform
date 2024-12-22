from django.db import models

from consumer.models import CustomUser
from teacher_app.models import Class, ExerciseQuestion, ExamQuestion, Exercise, Exam
from administrator_app.models import AdminExam, AdminExamQuestion


# Create your models here.
class Student(CustomUser):
    name = models.CharField(verbose_name="姓名", max_length=6)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="班级",
                                       null=True, blank=True, related_name='students')


