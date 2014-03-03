# -*- coding: utf-8 -*-
import os
import json
import ast

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from django.db import models
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect, render
from django.conf import settings
from rest_framework.renderers import JSONRenderer

from job_management import util
from job_management.forms import MathModelForm, JobForm, LoadcaseForm

from job_management.models import Job, MathModel, Loadcase, Task

from multigrid import calculate
from multigrid.solvers.modelicasolver import ModelicaLoadcase
from multigrid.solvers.pythonsolver import PythonSolver
from multigrid.solvers.modelicasolver import ModelicaSolver
from multigrid.multigrid import MultiGrid
from solvers import pythonsolver
from solvers import modelicasolver

import logging

logger = logging.getLogger('multigrid_web_app')

MODEL_TYPES = [pythonsolver.name, modelicasolver.name]

@login_required
def get_main(request):
	return redirect('/jobs/')


def register(request):
	if request.method == 'GET':
		return TemplateResponse(request, 'register.html')

	data, errors = {}, {}
	name = request.POST.get('username', 0)
	email = request.POST.get('email', 0)
	pass1 = request.POST.get('password1', 0)
	pass2 = request.POST.get('password2', 0)
	if name:
		data['name'] = name
	else:
		errors['name'] = u'Логин пользователя не введен'
	if email:
		data['email'] = email
	else:
		errors['email'] = u'Email пользователя не введен'

	if not pass1 or not pass2:
		errors['password'] = u'Пароль пользователя не введен'
	elif pass1 != pass2:
		errors['password'] = u'Введенный пароль не совпадает'

	if errors.keys():
		return TemplateResponse(request, 'register.html', {'errors': errors, 'data': data})

	user = User.objects.create_user(name, email, pass1)
	user.save()
	user = authenticate(username=name, password=pass1)
	if user.is_active:
		auth_login(request, user)
		return redirect("/jobs/")
	else:
		return HttpResponse("<html><body>Everything is BAD</body></html>")


def login(request):
	if request.method == 'GET':
		return TemplateResponse(request, 'login.html')

	data, errors = {}, {}
	username = request.POST.get('username', 0)
	password = request.POST.get('password', 0)
	user = None

	if not username:
		errors['username'] = u'Логин не введен'
	elif not password:
		errors['password'] = u'Пароль не введен'
	else:
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				auth_login(request, user)
			else:
				errors['data'] = u'Не верный логин или пароль'
		else:
			errors['data'] = u'Не верный логин или пароль'

	data['username'] = username

	if errors.keys():
		return TemplateResponse(request, 'login.html', {'errors': errors, 'data': data})
	else:
		return redirect('/jobs/')


def logout(request):
	auth_logout(request)
	return TemplateResponse(request, "logout.html")

@login_required
def profile(request):
	user = request.user
	if request.method == 'GET':
		data = {}
		data['email'] = user.email
		data['name'] = user.username
		return TemplateResponse(request, 'profile.html', {'data': data})

	email = request.POST.get('email', "")
	if email:
		user.email = email
		user.save()

	return redirect('/jobs/')




@login_required
def jobs_list(request):
	all_jobs, errors, data, num_jobs = {}, {}, {}, {}
	#num_paginator = Jobs.objects.filter(user=request.user).count()
	all_jobs = Job.objects.filter(user=request.user).order_by("-date")

	paginator = Paginator(all_jobs, 8)
	page = request.GET.get('page')

	try:
		data = paginator.page(page)
	except PageNotAnInteger:
		data = paginator.page(1)
	except EmptyPage:
		data = paginator.page(paginator.num_pages)

	return TemplateResponse(request, 'jobs.html',
							{'errors': errors, 'data': data, 'num_pages': xrange(1, paginator.num_pages + 1), 'flower': settings.FLOWER_ADDRESS})


@login_required
def search_job(request):
	if request.method == 'GET':
		return redirect('/jobs/')
	else:
		data, errors, = {}, {}
		query = request.POST.get('search_q', 0)
		data = Job.objects.filter(user=request.user, name__icontains=query).order_by("-date")
		return TemplateResponse(request, 'search_jobs.html', {'errors': errors, 'data': data, 'query': query})


@login_required
def delete_job(request, job_id):
	try:
		job = Job.objects.get(user=request.user, pk=job_id)
	except Job.DoesNotExist:
		raise Http404
	job.delete()
	return redirect('/jobs/')


@login_required
def create_job(request):
	if request.method == 'GET':
		loadcases = [(lc.name, lc.id) for lc in Loadcase.objects.all()]
		return TemplateResponse(request, 'create_job.html', {'loadcases': loadcases})

	name = request.POST.get('name', "")
	loadcases_ids = request.POST.getlist('loadcases')
	input_parameters = request.POST.get('input_parameters', "")

	# input parameters can be get from file
	input_file = request.FILES.get('input_file', None)
	if input_file:
		file_path = 'input_files/%s' % input_file
		default_storage.save(file_path, ContentFile(input_file.read()))
		input_parameters = input_file
		is_input_file = True
	else:
		is_input_file = False


	job = Job(name=name, user=request.user, input_params=input_parameters, is_input_file=is_input_file,
			  description=request.POST.get('job_description', ""))
	if job:
		job.save()
	for lc_id in loadcases_ids:
		job.loadcases.add(Loadcase.objects.get(id=lc_id))
	return redirect('/jobs/')

#@login_required
#def create_job(request):
#	if request.method == 'POST':
#		job_form = JobForm(request.POST)
#		if job_form.is_valid():
#			name = job_form.cleaned_data['name']
#			description = job_form.cleaned_data['description']
#			input_parameters = job_form.cleaned_data['input_parameters']
#			loadcases_ids = job_form.cleaned_data['loadcases']
#
#			print loadcases_ids
#
#			job = Job(name=name, user=request.user, input_params=input_parameters, description=description)
#
#			if job:
#				job.save()
#
#			#for lc_id in loadcases_ids:
#			#	job.loadcases.add(Loadcase.objects.get(id=lc_id))
#
#			return redirect('/jobs/')
#	else:
#		#mathmodels = [(model.name, model.id) for model in MathModel.objects.all()]
#		job_form = JobForm()
#	#return TemplateResponse(request, 'create_job.html', {'loadcases': loadcases, 'models': mathmodels, 'model_types': MODEL_TYPES})
#
#	#loadcases = [(lc.name, lc.id) for lc in Loadcase.objects.all()]
#	return render(request, 'create_job.html', {'form': job_form})


@login_required
def create_loadcase(request):
	if request.method == 'GET':
		mathmodels = [(model.name, model.id) for model in MathModel.objects.all()]
		#loadcase_form = LoadcaseForm()
		return TemplateResponse(request, 'create_loadcase.html', {'models': mathmodels})
	name = request.POST.get('loadcase_name', "")
	description = request.POST.get('loadcase_description', "")
	model_id = request.POST.get('model', 0)

	mathmodel = MathModel.objects.get(id=model_id)
	loadcase = Loadcase(name=name, description=description)
	loadcase.mathmodel = mathmodel
	if loadcase:
		loadcase.save()
	return redirect('/create_job/')


@login_required
def create_model(request):
	if request.method == 'GET':
		return TemplateResponse(request, 'create_model.html', {'model_types': MODEL_TYPES})
	model_type = request.POST.get('model_type', None)
	model = request.POST.get('model', "")

	file_model = request.FILES.get('file_model', None)
	if file_model:
		file_path = 'files/%s' % file_model
		default_storage.save(file_path, ContentFile(file_model.read()))
		model = file_model

	mathmodel = MathModel(name=model, type=model_type)
	if mathmodel:
		mathmodel.save()
	return redirect('/create_loadcase/')


@login_required
def edit_job(request, job_id):
	try:
		job = Job.objects.get(user=request.user, pk=job_id)
	except Job.DoesNotExist:
		raise Http404
	if request.method == 'GET':
		data = {}
		data['job'] = job
		return TemplateResponse(request, 'edit_job.html', {'data': data})
	else:
		job.name = request.POST.get('job_name', "")
		job.description = request.POST.get('job_description', "")
		job.input_params = request.POST.get('input_params', "")

		input_file = request.FILES.get('input_file', None)
		if input_file:
			file_path = 'input_files/%s' % input_file
			default_storage.save(file_path, ContentFile(input_file.read()))
			job.input_params = input_file
			job.is_input_file = True
		else:
			job.is_input_file = False

		job.status = 0.0
		job.save()
		return redirect('/jobs/')


@login_required
def calc_job(request, job_id):
	job = Job.objects.get(pk=job_id)
	job.status = 0.0
	# if job recalculated delete previous calculated results
	job_tasks = job.task_set.all()
	for task in job_tasks:
		task.delete()
	job.save()

	loadcases = []
	for web_lc in job.loadcases.all():
		mathmodel = web_lc.mathmodel
		lc = None
		if mathmodel.type == pythonsolver.name:
			pass
		elif mathmodel.type == modelicasolver.name:
			lc = ModelicaLoadcase(mathmodel.name)
		loadcases.append(lc)

	if job.is_input_file:
		params_list = get_input_list_from_file(job.input_params)
	else:
		input_parameters_string = job.input_params.split('|') # list of input parameters in string
		params_list = []
		for item in input_parameters_string:
			params_list.append(parse_input_params(item))

	task_ids = calculate(loadcases, params_list)

	for task_id, param in zip(task_ids, params_list):
		task = Task(task_id=task_id, input_params=param, job=job)
		task.save()

	return redirect('/jobs/')


@login_required
def get_job(request, job_id):
	data, errors = {}, {}
	try:
		job = Job.objects.get(user=request.user, pk=job_id)
		loadcases = job.loadcases.all()
		lc_names = [lc.name for lc in loadcases]
		#lc_names = util.decode_dict(lc_names)
		# concatenate all loadcases names
		result = ', '.join([x for x in lc_names])
	except Job.DoesNotExist:
		raise Http404
	data['job'] = job
	data['loadcases'] = result
	data['tasks'] = job.task_set.filter(is_finished=True)
	return TemplateResponse(request, 'job.html', {'errors': errors, 'data': data})

@login_required
def get_task(request, task_id):
	try:
		task = Task.objects.get(pk=task_id)
		data = dict()
		data['task'] = task
		result = ast.literal_eval(task.result)

		loadcases_list = result.keys()
		data['loadcases'] = loadcases_list

		if len(loadcases_list) is 1:
			loadcase = loadcases_list[0]
			data['loadcase'] = loadcase
			params = result[loadcase].keys()
			data['params'] = params
			if len(params) == 1:
				param = params[0]
				data['param'] = param
	except Task.DoesNotExist:
		raise Http404

	if request.POST:
		loadcase = request.POST.get('loadcase_name', None)
		param = request.POST.get('param_name', None)
		if loadcase and param:
			data['loadcase'] = loadcase
			data['params'] = result[loadcase].keys()
			data['param'] = param
			data['array'] = result[loadcase][param]
		elif loadcase:
			data['loadcase'] = loadcase
			data['params'] = result[loadcase].keys()


	return TemplateResponse(request, 'task.html', {'data': data})


def parse_input_params(param):
	parameter = json.loads(param, object_hook=util.decode_dict)
	return parameter


def get_input_list_from_file(file_name):
	"""
	Return input parameters list from file
	"""
	return []


class JSONResponse(HttpResponse):
	"""
	An HttpResponse that renders its content into JSON.
	"""
	def __init__(self, data, **kwargs):
		content = JSONRenderer().render(data)
		kwargs['content_type'] = 'application/json'
		super(JSONResponse, self).__init__(content, **kwargs)


def get_result(request, task_id):
	"""
	Return task result in JSON
	"""
	try:
		task = Task.objects.get(task_id=task_id)
		# replace ' on ", because sting in JSON surrounded with "
		return HttpResponse(task.result.replace("'", '"'))
	except Task.DoesNotExist:
		return Http404