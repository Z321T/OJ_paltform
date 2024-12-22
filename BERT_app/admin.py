from django.contrib import admin
from .models import (ProgrammingCodeFeature, ProgrammingReportFeature,
                     ReportStandardScore)

# Register your models here.
# admin.site.register(CodeFeature)
admin.site.register(ProgrammingCodeFeature)
admin.site.register(ProgrammingReportFeature)
admin.site.register(ReportStandardScore)
