__author__ = 'Lukasz'
from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from .models import Pensioner

class PensionerResource(ModelResource):
    class Meta:
        queryset = Pensioner.objects.all()
        resource_name = 'pensioner'