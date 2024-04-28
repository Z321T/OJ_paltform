from django.contrib import admin
from .models import Teacher, Class, Notification, Exercise, ExerciseQuestion, ExamQuestion, Exam, ReportScore

# Register your models here.
admin.site.register(Teacher)
admin.site.register(Class)
admin.site.register(Notification)
admin.site.register(Exercise)
admin.site.register(ExerciseQuestion)
admin.site.register(ExamQuestion)
admin.site.register(Exam)
admin.site.register(ReportScore)

