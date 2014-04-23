from django.contrib import admin

from job_management.models import Project, Job, Loadcase, MathModel

#class ProjectAdmin(admin.ModelAdmin)


admin.site.register(Project)
admin.site.register(Job)
admin.site.register(Loadcase)
admin.site.register(MathModel)