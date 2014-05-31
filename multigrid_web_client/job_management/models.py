from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
	user = models.ForeignKey(User)
	name = models.CharField(max_length=255)
	date = models.DateTimeField(auto_now_add=True, blank=True)
	description = models.TextField()

	def __unicode__(self):
		return self.name


class MathModel(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	type = models.TextField()
	content = models.TextField()

	def __unicode__(self):
		return self.name


class Loadcase(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	solver_params = models.TextField()
	mathmodel = models.ForeignKey(MathModel)

	def __unicode__(self):
		return self.name


class Job(models.Model):
	project = models.ForeignKey(Project)
	name = models.CharField(max_length=255)
	date = models.DateTimeField(auto_now_add=True, blank=True)
	status = models.FloatField(default=0.0)
	description = models.TextField()
	loadcases = models.ManyToManyField(Loadcase)
	input_params = models.TextField()
	is_input_file = models.BooleanField(default=False)
	result_params = models.TextField()
	error_count = models.IntegerField(default=0)
	#is_finished = models.BooleanField(default=False)

	def __unicode__(self):
		return self.name


class Task(models.Model):
	job = models.ForeignKey(Job)
	task_id = models.TextField()
	input_params = models.TextField()
	result = models.TextField()
	is_error = models.BooleanField(default=False)
	log = models.TextField()
	is_finished = models.BooleanField(default=False)

	def __unicode__(self):
		return self.name


