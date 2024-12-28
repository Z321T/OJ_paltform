from django.contrib import admin
from .models import Scores, ExerciseCompletion, ExerciseQuestionCompletion, StudentCode, ExamCompletion, \
    ExamQuestionCompletion, AdminExamCompletion, AdminExamQuestionCompletion

# Register your models here.
admin.site.register(Scores)
admin.site.register(ExerciseCompletion)
admin.site.register(ExerciseQuestionCompletion)
admin.site.register(ExamCompletion)
admin.site.register(ExamQuestionCompletion)
admin.site.register(AdminExamCompletion)
admin.site.register(AdminExamQuestionCompletion)
admin.site.register(StudentCode)
