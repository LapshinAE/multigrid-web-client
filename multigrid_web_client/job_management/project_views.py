from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from job_management.models import Project


@login_required
def projects(request):
	projects = Project.objects.filter(user=request.user).order_by("-date")

	paginator = Paginator(projects, 8)
	page = request.GET.get('page')

	try:
		data = paginator.page(page)
	except PageNotAnInteger:
		data = paginator.page(1)
	except EmptyPage:
		data = paginator.page(paginator.num_pages)

	return TemplateResponse(request, 'projects/projects.html',
							{'data': data, 'num_pages': xrange(1, paginator.num_pages + 1)})


@login_required
def search_project(request):
	if request.method == 'GET':
		return redirect('/projects/')
	else:
		data, errors, = {}, {}
		query = request.POST.get('search_q', 0)
		data = Project.objects.filter(user=request.user, name__icontains=query).order_by("-date")
		return TemplateResponse(request, 'projects/projects_search.html', {'errors': errors, 'data': data, 'query': query})


@login_required
def delete_project(request, project_id):
	try:
		project = Project.objects.get(user=request.user, pk=project_id)
		project.delete()
	except Project.DoesNotExist:
		raise Http404
	return redirect('/projects/')


@login_required
def create_project(request):
	if request.method == 'GET':
		return TemplateResponse(request, 'projects/create_project.html')

	name = request.POST.get('name', "")
	project = Project(name=name, user=request.user, description=request.POST.get('description', ""))
	if project:
		project.save()
	return redirect('/projects/')