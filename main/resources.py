
from tastypie.resources import ModelResource
from tastypie_jqgrid.resources import JqGridResourceMixin
from tastypie.constants import ALL
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from django.contrib.auth import get_user_model
from django.utils import timezone
from tastypie.resources import fields

from .models import Pensioner

class MyAuthentication( SessionAuthentication ):
    '''
    Authenticates everyone if the request is GET otherwise performs
    ApiKeyAuthentication.
    '''
    def is_authenticated(self, request, **kwargs):
        if request.method in ['GET','PATCH']:
            return True
        return super( MyAuthentication, self ).is_authenticated( request, **kwargs )

class MyAuthorization( DjangoAuthorization ):
    '''
    Authorizes every authenticated user to perform GET, for all others
    performs DjangoAuthorization.
    '''

    def is_authorized(self, request, object=None):
        if request.method in ['GET','PATCH']:
            return True
        else:
            return super( MyAuthorization, self ).is_authorized( request, object )

_PENSIONER_FIELDS = ('reference', 'title','forename', 'surname')
class PensionerResource(JqGridResourceMixin, ModelResource):
    class Meta(JqGridResourceMixin.Meta):
        queryset = Pensioner.objects.all()
        resource_name = 'pensioner'
        #filtering = {'pensioner': ALL}
        filtering = dict([(k, ALL) for k in _PENSIONER_FIELDS])
        authentication = MyAuthentication()
        authorization = MyAuthorization()
        allowed_methods = ['get','patch']
