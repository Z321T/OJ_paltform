from django.contrib import admin
from .models import (Teacher, Class, Notification, ReportScore,
                     Exercise, ExerciseQuestion, ExamQuestion, Exam, ExerciseQuestionTestCase, ExamQuestionTestCase)

# Register your models here.
admin.site.register(Teacher)
admin.site.register(Class)
admin.site.register(Notification)
admin.site.register(Exercise)
admin.site.register(ExerciseQuestion)
admin.site.register(ExerciseQuestionTestCase)
admin.site.register(Exam)
admin.site.register(ExamQuestion)
admin.site.register(ExamQuestionTestCase)
admin.site.register(ReportScore)

