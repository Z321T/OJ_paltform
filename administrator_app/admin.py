from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import Administrator, AdminNotification, ProgrammingExercise, AdminExam, AdminExamQuestion


class AdministratorAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


# Register your models here
admin.site.register(Administrator, AdministratorAdmin)
admin.site.register(AdminNotification)
admin.site.register(ProgrammingExercise)
admin.site.register(AdminExam)
admin.site.register(AdminExamQuestion)
