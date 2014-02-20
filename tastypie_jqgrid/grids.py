from copy import deepcopy
from django.conf import settings
from tastypie_jqgrid.columns import Column, BaseColumn
from tastypie_jqgrid.utils import get_default_options, deep_update, \
    LazyJSONEncoder
import json

class MgBaseOptions(object):
    """ base Options class, fills automatically from given object
        or kwargs, provides iterability
    """    
    def __init__(self, opts=None, **kwargs):
        if opts:
            opts = opts.__dict__.items()
        else:
            opts = []
        if len(kwargs.items()) > 0:
            opts.extend(kwargs.items())
        for key, value in opts:
            if key[:2] == '__':
                continue
            setattr(self, key, value)
            
    def __iter__(self):
        #return ((k, v) for k, v in self.__dict__.iteritems() if k[:1] != '_')
        return ((k, v) for k, v in self.__dict__.items() if k[:1] != '_')

class JqGridOptions(MgBaseOptions):
    # what tastypie Resource to use in grid.
    # the Resource has to be registered in urls. 
    grid_resource = None
    
    # is filtering toolbar enabled (jqGrid: Toolbar Searching)
    filtering_toolbar = False
    
    # pager element (jQuery selector, like '#pager' or 'div.grid-pager') . if None, pager won't be visible    
    pager_selector = None    
    # pager buttons.
    pager_buttons = {}
    # options passed to pager
    pager_options = {}
    
    # when set to True, each row is set in inline editing mode when clicked (selected) 
    automatic_inline_editing = False
   
    # by default, we have "infinite scroll". If set to False, we'll have pagination instead.
    # When False, you'll need to enable pager navigator (set pager_selector) to allow user switch pages
    scroll = True
   
    # if set, all the colmodel columns which do not specify 'editable' will be set to True 
    columns_editable_by_default = False
    # name and order of a default sort column, in django format: "-column" or "column". translates to "sortname" in jqGrid options
    default_sort = None   
    
    # low-level config (dict of config options for jqGrid and mGrid)
    grid_options = {}
    
    # grid height
    height = None
    # how many rows display by default
    rows_count = None


class MgGridMetaclass(type):
    def __new__(cls, name, bases, attr):
        
        # set_column_name sets the name and returns object itself (it is "chainable").
        columns = [attr.pop(field_name).set_column_name(field_name) for field_name, obj in list(attr.items()) if isinstance(obj, BaseColumn)] 
        columns.sort(key = lambda x: x._creation_counter)
        attr['columns'] = columns
        
        # classes which we need to handle "special" way (handle inheritance etc)
        classes = {'GridOptions': '_grid_options'}
        for opt_klass_name, opt_attr_name in classes.items():
            options = attr.pop(opt_klass_name, None) or type(opt_klass_name)

            initial_options = frozenset(dir(options))
            for base in bases:
                if hasattr(base, opt_attr_name):
                    for fname, value in base._grid_options:
                        if fname not in initial_options:
                            setattr(options, fname, value)
    
            attr[opt_attr_name] = JqGridOptions(options)
        return super(MgGridMetaclass, cls).__new__(cls, name, bases, attr)
    

class JqGridBase(object, metaclass=MgGridMetaclass):
    #__metaclass__ = MgGridMetaclass
    

    def get_grid_resource(self):
        """
            return an instance of Resource 
            which is a data source for this grid
        """
        if not self._grid_options.grid_resource:
            raise Exception("Required field 'grid_resource' not set in the JqGrid subclass.")
        if not hasattr(self, '_grid_resource_instance'):
            self._grid_resource_instance = self._grid_options.grid_resource()
        
        return self._grid_resource_instance
    
    # TODO: move to JqGridOptions?
    def get_grid_final_options(self, user):
        """ 
            this function returns the final grid options
            it merges the 
                 * default options (from settings),
                 * grid-specific options (returned by get_grid_options)
                 * dynamicaly-generated options, based on the GridOptions and other subclasses
                 * colModel
                 * data url, edit url etc.
        """
        
        resourceEndpointUrl = self.get_grid_resource().get_resource_uri()

        
        grid_options = deepcopy(get_default_options())
        grid_options = deep_update(grid_options, self.get_grid_options(user))
        
        
        if self._grid_options.filtering_toolbar:
            grid_options = deep_update(grid_options, { 
                                 'mGrid': {
                                           'filter_toolbar': {'stringResult': True}
                                        }
                                 })            
        if self._grid_options.pager_selector:
            grid_options = deep_update(grid_options, {'pager': self._grid_options.pager_selector, 
                                  'mGrid': {
                                        'pager_buttons': self._grid_options.pager_buttons, 
                                        'pager_options': self._grid_options.pager_options
                                  }
                                })
        
        
        auto_attrs = ('scroll', 'height', 'rows_count')
        auto_attrs_aliases = {'rows_count': 'rowNum'}
        for attr in auto_attrs:
            if hasattr(self._grid_options, attr) and getattr(self._grid_options, attr) is not None:                
                grid_options[auto_attrs_aliases.get(attr, attr)] = getattr(self._grid_options, attr)
        
        if self._grid_options.default_sort:
            # translate from "-column" to "desc", "column"
            sort = self._grid_options.default_sort
            if sort.startswith('-'):            
                grid_options['sortorder'] = 'desc'
                sort = sort[1:]
            grid_options['sortname'] = sort

        if self._grid_options.automatic_inline_editing:
            grid_options = deep_update(grid_options, { 
                             'mGrid': {
                                       'automatic_inline_editing': True
                                    }
                             })      

        
        # transform list of columns to the colModel dict used by jqGrid.js        
        user_colmodel = self.get_grid_colmodel(user)
                    
        # we need these *special* fields to be accessible, so add them & make them invisible.    
        final_colmodel = user_colmodel + \
            [{'name': f, 'hidden': True} for f in ('_pk', '_unicode', 'resource_uri', '_model_uri')]
                    
        grid_options = deep_update(grid_options,{
            'url': resourceEndpointUrl,
            'editurl': resourceEndpointUrl,
            'colModel': final_colmodel,            
        }) 
                
        return grid_options
    
    def get_grid_options(self, user):
        return self._grid_options.grid_options
    
    def get_grid_final_options_js(self, user):
        """ 
            return the JSON serialzed grid config
        """
        
        grid_options = self.get_grid_final_options(user)
        indent = 4 if settings.DEBUG else None
        grid_options = json.dumps(grid_options, cls = LazyJSONEncoder, sort_keys = True, indent = indent)
        return grid_options
    
    def get_columns(self):
        """ returns all the fields which are subclasses of BaseColumn """
        return self.columns # property created by the Metaclass
    
    def get_grid_colmodel(self, user, **kwargs):
        """ returns the grid colmodel (list of Column instances)            
            you might override it if you need.
            by default it returns all the fields which subclass BaseColumn
            otherwise it generates very basic colmodel based on Resource fields with attributes
        """
            
        columns = self.get_columns()
        if not columns:            
            fields = self.get_grid_resource().fields        
            columns = [Column(name = field_name) for field_name, field in fields.items() if field.attribute]
            
        colmodels = [x.to_colmodel_dict() for x in columns]
        if self._grid_options.columns_editable_by_default:
            for mod in colmodels:
                if not 'editable' in mod:
                    mod['editable'] = True
        
        return colmodels
    
class JqGrid(JqGridBase):
    pass