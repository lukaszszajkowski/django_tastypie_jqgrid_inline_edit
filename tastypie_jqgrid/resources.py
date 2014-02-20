from tastypie_jqgrid.serializers import JqGridSerializer
from tastypie_jqgrid.paginators import JqGridPaginator

#TODO: use Metaclass for Meta handling?
class JqGridResourceMixin(object):                
    class Meta:        
        include_resource_uri = True        
        serializer = JqGridSerializer()
        paginator_class = JqGridPaginator
        
    def dehydrate(self, bundle):
        """ _pk && _unicode are very useful :) """ 
        sup_bundle = super(JqGridResourceMixin, self).dehydrate(bundle)
        sup_bundle.data['_unicode'] = str(bundle.obj)
        #sup_bundle.data['_unicode'] = unicode(bundle.obj)
        sup_bundle.data['_pk'] = bundle.obj.pk
        if hasattr(bundle.obj, 'get_absolute_url'):
            url = bundle.obj.get_absolute_url()
            if url is not None:
                sup_bundle.data['_model_uri'] = url
        return sup_bundle