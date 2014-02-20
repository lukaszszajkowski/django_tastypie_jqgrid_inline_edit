from collections import OrderedDict
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from tastypie.resources import ModelResource
from tastypie_jqgrid.utils import JSFunc, deep_update
import collections

class BaseColumn(object):
    # Resource attribute name
    name = None
    
    
    # trick used by django Forms to keep fields order.
    _creation_counter = 0
     
    def __init__(self, *args, **kwargs):
        self._creation_counter = BaseColumn._creation_counter
        BaseColumn._creation_counter += 1
        super(BaseColumn, self).__init__(*args, **kwargs)   
    
    def get_column_name(self):
        # self._name might be assigned by Grid while iterating fields of type Column.
        if self.name is not None:
            return self.name               
        return self._name
        
    
    def set_column_name(self, name):
        """ chainable method used with iterator in the metaclass of JqGrid """
        self._name = name
        return self
     
class Column(BaseColumn):
    """ represents single item of colModel """    
    # label
    label = None
    # column width
    width = None
    # is column editable? None means it'll be determined automatically (see columns_editable_by_default of grid)
    editable = None
    # JS formatter
    formatter = None
    # is column visible?
    hidden = None
    # show the column when editing 
    edithidden = None
    # is search enabled on this column?
    search = None
    
    # available comparison methods (like ['eq','lt','le']...). See "sopt" in "searchoptions" in jqGrid documentation.
    # please note that currently none of the negated operators is supported.
    # The first provided value is used for Toolbar Searching
    search_opts = ('bw', 'eq','lt','le','gt','ge','in','ew','cn')
    
    def __init__(self, label = None, *args, **kwargs):
        # name is no longer required, as it's delcared by colname = Column() ...
        #self.name = name
        self.label = label  
        for arg, value in kwargs.items():
            if not hasattr(self, arg): # all the attributes are explicitely predefined. don't allow misspelled ones. 
                raise Exception("Unexpected keyword argument %s" % arg)
            setattr(self, arg, value)
        return super(Column, self).__init__(*args)

    def get_edittype(self):
        return None
    
    def get_editoptions(self):
        """ build colmodel's editoptions dict""" 
        return None
    
    def get_formatoptions(self):
        """ build colmodel's formatoptions """
        return None
    
    def get_stype(self):
        """ return column stype (search type) """
        return None
    
    def get_searchoptions(self):
        """ build colmodel's searchoptions dict"""        
        if self.search_opts: 
            return { 'sopt': self.search_opts}
        
    def get_formatter(self):
        return self.formatter
        
    def to_colmodel_dict(self):
        colmodel = {'name': self.get_column_name()}        
        for k in ('label', 'width', 'editable', 'hidden', 'search'):            
            v = getattr(self, k)            
            if v is not None:
                colmodel[k] = v
        
        # callable get_foo() -> foo is an colmodel key.
        callable_subopts = ('editoptions', 'formatoptions', 'searchoptions', 'edittype', 'formatter', 'stype')
        for mname in callable_subopts:
            method = getattr(self, 'get_%s' % mname)
            opts = method()
            if opts:
                colmodel[mname] = opts
        
        if self.edithidden is not None:
            colmodel['editrules'] = {'edithidden': self.edithidden}
        
        return colmodel


class IntegerColumn(Column):
    formatter = 'integer'

class NumericColumn(Column):
    formatter = 'number'
    
class DecimalColumn(NumericColumn):    
    decimal_places = 3
    def get_formatoptions(self):
        return {'decimalPlaces': self.decimal_places}
    

class DateColumn(Column):
    # jqGrid display formatter
    formatter = 'date'
    # jqGrid date formatter srcformat & newformat 
    date_srcformat = 'Y-m-d'
    date_newformat = 'd/m/Y'
    datefmt = None
    
    # enable datepicker for Form Editing
    datepicker_edit = False
    # enable datepicker for Toolbar Search 
    datepicker_search_tb = False
    # datepicker date format
    datepicker_date_format = 'yy-mm-dd'
    def _opts(self):
        return  {
                     #size: 10, maxlengh: 10,
                    'dataInit': JSFunc("function(element) { \
                        $(element).datepicker({dateFormat: '%(date_fmt)s'}) \
                    }" % {'date_fmt': self.datepicker_date_format})
                }
    
    def to_colmodel_dict(self):
        data = super(DateColumn, self).to_colmodel_dict()
        if self.datefmt:
            data['datefmt'] = self.datefmt
        return data
    
    def get_editoptions(self):
        if self.datepicker_edit:
            return self._opts()
    
    def get_formatoptions(self):
        return {
                'srcformat': self.date_srcformat,
                'newformat': self.date_newformat
                }
                
    def get_searchoptions(self):        
        if self.datepicker_search_tb:
            opts =  self._opts()
            # dt is special type handled by mGrid (in order not to append any operator like __iexact)
            # otherwise date is compared like a string, not like a date.            
            sopt = self.search_opts or ('dt',)
            # if no 'dt' filter (inherited value)
            if not 'dt' in sopt:
                sopt = ['dt'] + list(sopt)
            opts.update({
                         'sopt': sopt,  
                         })
            return opts
#TODO: use some date & time picker here.
class DateTimeColumn(DateColumn):    
    date_srcformat = "Y-m-d\\TH:i:s"
    date_newformat = 'd/m/Y H:i'
    
    
class AutoCompleteColumnMixin(object):
    """ 
    Enables jQuery UI Autocomplete on the column.
    
    For Form Editing, it creates two fields, one - visible - for label & completion (this one is NOT being sent to the server),
    while the second one - for storing the actual value - is invisible, but sent to the server.
    This is because in most cases we need to send the related object's PK, not the label.
    target_field is the name of the Resource field (not Grid column!! There might be no column for this field!!)
    to which the selected autocomplete VALUE will be sent.    
    
    For Toolbar Search, there's only one field, because it does lookup by the attribute
      
    It's mixin since it could be used with other column types in future. """
    # data source (TastyPie Resource)
    resource = None
    # what field to compare on?
    comp_field = None 
    # what field to display?
    label_field = None
    # what should be OUTPUT field name (i.e. that should be the name of ID field?)
    target_field = ''
    def get_editoptions(self, *args, **kwargs):        
        opts = super(AutoCompleteColumnMixin, self).get_editoptions(*args, **kwargs) or {}
        values = {
                  'url': self.resource.get_resource_uri(),
                  'compfield': self.comp_field,
                  'labelfield': self.label_field or self.comp_field,
                  'targetfield': self.target_field 
                 }        
        #TODO: move JS code to mGrid routines, here just simple function(){  call_routine_with_params(); }
        opts['dataInit'] = JSFunc(r"""function(element) {
                        var $elem = $(element),
                        orgname = $elem.attr('name'),
                        newname = orgname + '_ac_display',
                        orgid = $elem.attr('id'),
                        newid = orgid + '_ac_value',
                        targetname = "%(targetfield)s",
                        // it can't be type:hidden as jqGrid's getFormData doesn't handle it :(
                        $final_elem = $('<input/>')                            
                            .css('display', 'none')                            
                            .attr('type', 'text').attr('name', orgname).attr('id', newid)
                            .attr('data-mgrid-clear-onshow', 'true');
                        // set target field's name 
                        if (targetname != '')
                            $final_elem.attr('name', targetname);
                                               
                                                
                        $elem.attr('name', newname) 
                        setTimeout(function(){
                            // remove the FormElement class so it won't be serialized by jqGrid's getFormData    
                            $final_elem.removeClass('FormElement').insertAfter($elem);
                            $elem.removeClass('FormElement').attr('data-mgrid-formelement');                            
                            $elem.autocomplete({
                                source:  function(request, response) {
                                  return $.getJSON("%(url)s?%(compfield)s__startswith=" + $.trim(request.term), null, function(data) {
                                      var x;
                                    return response((function(){
                                        var _results = [];
                                        $.each(data.objects, function(idx, itm){
                                            _results.push({
                                              "label": itm.%(labelfield)s,
                                              "value": itm._pk
                                            });
                                        });
                                        return _results;
                                    })()); // end of response
                                  }); // end of getJSON callback
                                },
                                select: function(event, ui) {
                                    var selectedObj = ui.item,
                                        $this = $(this),
                                        org_id = $this.attr('id'), 
                                        sel_id = org_id + '_ac_value';
                                        $org_field = $('#'+sel_id); // original field              
                                        // it now has the value, so might be serialized. add FormElement. see issue #8                          
                                        $org_field.val(selectedObj.value).addClass('FormElement'); 
                                        $this.val(selectedObj.label) ;
                                    return false;
                                }
                            }); 
                        }, 300); 
                   }""" % values)
        return opts
    
    def get_searchoptions(self,):
        opts =  super(AutoCompleteColumnMixin, self).get_searchoptions()
        values = {
                  'url': self.resource.get_resource_uri(),
                  'compfield': self.comp_field,
                  'labelfield': self.label_field or self.comp_field,
                  'targetfield': self.target_field 
                 }
        opts.update({
            'sopt': 'dt',
            'dataInit': JSFunc(r"""function(element) {
                        var $elem = $(element);                        
                        setTimeout(function(){                             
                            $elem.autocomplete({
                                source:  function(request, response) {
                                  return $.getJSON("%(url)s?%(compfield)s__startswith=" + $.trim(request.term), null, function(data) {
                                      var x;
                                    return response((function(){
                                        var _results = [];
                                        $.each(data.objects, function(idx, itm){
                                            _results.push({
                                              "label": itm.%(labelfield)s,
                                              "value": itm.%(labelfield)s
                                            });
                                        });
                                        return _results;
                                    })()); // end of response
                                  }); // end of getJSON callback
                                }                                
                            }); 
                        }, 300); 
                   }""" % values)            
        })
        return opts
    
  
class AutoCompleteColumn(AutoCompleteColumnMixin, Column):
    pass


class SelectColumnMixin(object):
    # Model class, 
    # QuerySet instance,
    # list of 2-tuples or list of single values
    # or a dict of value: label
    source = None
    
    # what column to use for select option value?
    value_column = 'pk'
    # what column to use for select option display? If None, unicode(model) will be used
    label_column = None
    
    # is multi select?
    multiple = False
    # multi select size
    size = None
    
    # enable for toolbar search
    enabled_toolbarsearch = True
    # enable for form editing
    enabled_formediting = True
    
    def get_choices(self, for_search = False):
        """ returns a list of 2-tuples (value, display) """
        src = self.source
        if isinstance(src, ModelBase):
            src = src._default_manager.all()                
        if isinstance(src, QuerySet):
            res = [(getattr(x, self.value_column), 
                    getattr(x, self.label_column) if self.label_column else str(x)) for x in src]
                    #getattr(x, self.label_column) if self.label_column else unicode(x)) for x in src]
        elif isinstance(src, dict):
            #TODO: use value_column and label_column here?
            res = [(x['value'], x['label']) for x in src]
        elif isinstance(src, collections.Iterable):
            res = []
            for x in src:
                if isinstance(x, (list,tuple)):
                    res.append(x)
                else:
                    res.append((x,x))
        elif isinstance(src, ModelResource):
            return False # no choices, however - we know to build them dynamically
        else:
            raise ImproperlyConfigured("No source provided for SelectColumn or source is not in a valid format")
        if for_search:
            res.insert(0, ('', '-'))
        return OrderedDict(res)
    
    def _get_common_options(self, for_search = False):
        res = {}
        choices = self.get_choices(for_search)
        if choices is not False: # if False, it's URI of Resource to build select options client-side
            res['value'] = choices
        else:
            # FIXME: format appended - ugly, but jqGrid calls .get and not .getJSON                
            # FIXME: 1000 rows - ugly, but TastyPie limits it. Anyway, loading more than 50-200 items into select is not a smart way from UX point of view.                            
            res['dataUrl'] = self.source.get_resource_uri() + '?format=json&rows=1000'
            res['buildSelect'] = JSFunc(""" function(data, a, b){
                var jsondata = $.parseJSON(data);
                if (parseInt(jsondata.total) > 1)
                    alert("mGrid: while loading the data for select, it seems thera are more than 1000 items available. Ask the developer to change the widget, as the select is limited to 1000 options at once");
                var res = "<select>";
                $(jsondata.rows).each(function(idx, row){
                    res += '<option value="'+row.resource_uri+'">'+row['%(label_attr)s']+'</option>';
                });
                return res + "</select>";
            }""" % {'label_attr': self.label_column or '_unicode'})
            
            
        
        if self.multiple is not None and self._use_customselect():
            res.update({
                    'multiple': self.multiple,
                    'custom_element': JSFunc(r"""function (value, options) {
                        return $.jgrid.createEl.call(this, "select",
                            $.extend(true, {}, options, {custom_element: null, custom_value: null}),
                        value,{},$.jgrid.ajaxOptions);}"""),
                                
                    'custom_value': JSFunc(r"""function ($elem, operation, value) {
                        if (operation === "get") {
                            return $elem.val();
                        } else if (operation === "set"){
                            if (!$.isArray(value))
                            {
                                if (value.indexOf(',')) // comma separated value ... oh, why jqGrid?! why?!
                                    value = value.split(',');
                                else
                                    value = [value];
                            }                            
                            // deselect all
                            $elem.find('option').prop('selected', false);
                            $.each(value, function(idx, item){
                                $elem.find('option[value="'+item+'"]').prop('selected', true);                                
                            });
                        }}""")
                    })
            
        
        if self.size is not None:
            res['size'] = self.size
            
        return res
    
    def get_editoptions(self):
        data = super(SelectColumnMixin, self).get_editoptions() or {}
        if self.enabled_formediting:
            res = self._get_common_options()            
            data = deep_update(data, res)
        return data
    
    def _use_customselect(self):
        return isinstance(self.source, ModelResource)    
        
    def get_edittype(self):
        if not self.enabled_formediting:
            return super(SelectColumnMixin, self).get_edittype()
        if self._use_customselect():
            return 'custom'    
        return 'select'
    
    def get_stype(self):
        if not self.enabled_toolbarsearch:
            return super(SelectColumnMixin, self).get_stype()
        if self._use_customselect():
            return 'custom'    
        return 'select'
    
    def get_searchoptions(self):
        data = super(SelectColumnMixin, self).get_searchoptions()
        if self.enabled_toolbarsearch:
            res = self._get_common_options(for_search = True)            
            data = deep_update(data, res)
        return data    
    
class SelectColumn(SelectColumnMixin, Column):
    pass
