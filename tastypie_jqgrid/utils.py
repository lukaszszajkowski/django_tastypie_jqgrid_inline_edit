from django.conf import settings
from django.utils.encoding import force_text
from django.utils.functional import Promise
from django.utils.translation import ugettext_lazy as _
import collections
import json
import re



class JSFunc(object):
    """ class that wraps the string into !!JSFUN!!<content>!!JSFUN!! blocks.
        While serializing, these blocks are removed together with quote mark (' or ")
        That way, the provided string is not quoted, so it can be a JS functon.
    """
    _value = None
    def __init__(self, value):
        self._value = value
    @property
    def value(self):
        return u'!!JSFUN!!%s!!JSFUN!!' % self._value
    def __str__(self):
        return self.value() 

class LazyJSONEncoder(json.JSONEncoder):
    """ this custom JSON encoder does two things:
        * it forces any "lazy" function to be evaluated (like ugettext_lazy or JSFunc [above] ) so it can be serialized 
        * it removes !!JSFUN!! markers (appended by JSFunc) together with the quotation marks so the function code can be passed.  
    """
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        if isinstance(obj, JSFunc):
            return obj.value        
        return super(LazyJSONEncoder, self).default(obj)
    # TODO: is there any better way to avoid this?
    def encode(self, o):
        val = super(LazyJSONEncoder, self).encode(o)
        
        js_body_regex = re.compile(r'(!!JSFUN!!)(.*?)(!!JSFUN!!)')        
        val = js_body_regex.sub(lambda s: ''.join([s.group(1), 
                                                   # in code body, replace all the escaped sequences
                                                   # (\n, \", \' ... )
                                                   #s.group(2).replace(r'\n', '\n'),

                                                   bytes(s.group(2), "utf-8").decode("unicode_escape"),
                                                   #s.group(2).decode("string-escape"), #replace(r'\n', '\n'),
                                                   s.group(3)]), val)
        
        patterns = ('(\'|")!!JSFUN!!', '!!JSFUN!!(\'|")')
        for pattern in patterns:
            if re.search(pattern, val):
                val = re.sub(pattern, '', val)
        return val
            
    
# deep update a dict,
# updating also the "sub" dicts.
def deep_update(d, u):
    #for k, v in u.iteritems():
    for k, v in u.items():

        if isinstance(v, collections.Mapping):
            r = deep_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
    
__grid_default_options = {
        'datatype': 'json',                
        'ajaxRowOptions': { 'contentType': "application/json", 'type': "PATCH" }, 
        'mtype': 'GET',
        'jsonReader': {
            'root': 'rows',
            'page': 'page',
            'total': 'total',
            'records': 'records',
            'repeatitems': False,
            'cell': 'cell',
            'id': 'id',
            'userdata': 'userdata',
            'subgrid': {
                'root': 'rows', 
                'repeatitems': False, 
                'cell': 'cell',
            }
        },
        'viewrecords': False,        
        'gridview': True,
        'autowidth': True,
        'shrinkToFit': False,
        #'height': '100%',
        'altRows': True,
        'empyrecords': _(u"No results to display"),
        'loadtext': _(u"Loading ..."),
        'loadui': 'block',
        'scroll': True,
        'sortable': True,
        #'rownumbers': True,
        'caption': '', 
        'toolbar': [True, 'top'],    
        'rowNum': 10,
        'rowList': [10, 20, 30],
    }

def get_default_options():
    try:
        return settings.grid_default_options
    except AttributeError:
        pass
    return __grid_default_options