from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
					# User accounts
					url(r'^$',          'job_management.views.get_main'),
					url(r'^login/$',    'job_management.views.login'),
					url(r'^logout/$',   'job_management.views.logout'),
					url(r'^register/$', 'job_management.views.register'),
					url(r'^profile/$', 'job_management.views.profile'),

					# Projects
					url(r'^jobs/$', 'job_management.views.jobs_list'),
					url(r'^job/(?P<job_id>\d+)/$', 'job_management.views.get_job'),
					url(r'^create_job/$', 'job_management.views.create_job'),
					url(r'^create_loadcase/$', 'job_management.views.create_loadcase'),
					url(r'^create_model/$', 'job_management.views.create_model'),
					url(r'^search_job/$', 'job_management.views.search_job'),
					url(r'^delete_job/(?P<job_id>\d+)/$', 'job_management.views.delete_job'),
					url(r'^edit_job/(?P<job_id>\d+)/$', 'job_management.views.edit_job'),
					url(r'^calc_job/(?P<job_id>\d+)/$', 'job_management.views.calc_job'),
					url(r'^task/(?P<task_id>\d+)/$', 'job_management.views.get_task'),

					#JSON API
					url(r'api/get_result/(?P<task_id>[0-9a-zA-Z\-]+)/$', 'job_management.views.get_result'),
					url(r'api/get_ids/(?P<job_name>\w+)/$', 'job_management.views.get_ids'),
					url(r'api/get_results_from_job/(?P<job_name>\w+)/$', 'job_management.views.get_results_from_job'),


					# Admin
					url(r'^admin/', include(admin.site.urls)),
					)