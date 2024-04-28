from django.contrib import admin
from .models import (Student, Score, ExerciseCompletion, ExerciseQuestionCompletion,
                     ExamCompletion, ExamQuestionCompletion, AdminExamCompletion, AdminExamQuestionCompletion,)

# Register your models here.
admin.site.register(Student)
admin.site.register(Score)
admin.site.register(ExerciseCompletion)
admin.site.register(ExerciseQuestionCompletion)
admin.site.register(ExamCompletion)
admin.site.register(ExamQuestionCompletion)
admin.site.register(AdminExamCompletion)
admin.site.register(AdminExamQuestionCompletion)
