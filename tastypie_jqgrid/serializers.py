from tastypie.serializers import Serializer
import simplejson

class JqGridSerializer(Serializer):    
    def to_json(self, data, options=None):        
        data = self.to_simple(data, options)
                
        #if not data.has_key('meta') or not data.has_key('objects'):
        if not 'meta' in data or not 'objects' in data:

            return super(JqGridSerializer, self).to_json(data, options)
        
        meta = data['meta']

        jqgrid_data = {
            'page': '%s' % (meta['offset'] / meta['limit'] + 1),
            'total': '%s' % (meta['total_count'] / meta['limit'] + (1 if meta['total_count'] % meta['limit'] else 0)),
            'records': '%s' % meta['total_count'],            
            'rows' : data['objects']
        }
        
        return simplejson.dumps(jqgrid_data, sort_keys=True)
    
    def from_json(self, content):                
        data = simplejson.loads(content)
        if 'oper' in data:
            del data['oper']
        return data 