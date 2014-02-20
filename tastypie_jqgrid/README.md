# django-tastypie-jqgrid

``django-tastypie-jqgrid`` project aims to fill the gap between jqGrid and Django, using TastyPie. 

Currently it supports:


* sorting
* paging
* toolbar filtering (except *negated* operators as for now)
* form editing (editing in a popup)
    * modifying existing record
    * creating new records
    * deleting records
* DatePicker integration (both for searching and editing)
* AutoComplete integration (both for searching and editing)
* SelectColumn for select widget in edit or search forms
* JavaScript generation (no JS knowledge needed for basic usage of grid)

please consider it **alpha** release as for now. 
There *might* (and probably *will*) be backward-compatibility breaking changes in close future, as the 
project is under heavy development.      

## installation

There are no package releases yet. If you do want to use it in the current version, 
the only way is to do ``hg clone http://bitbucket.org/migajek/django-tastypie-jqgrid`` 

## requirements

The code requires ``django-tastypie`` (**current repository version**, as of 2013-01-11, since the latest release - 0.9.11 - 
is a bit outdated.)

Demo project requires Django 1.5, it should however be possible to run on older versions with little modifications. 
 
## screenshots
![django-tastypie-jqgrid screen](http://i.imgur.com/9N9AG.png)
![django-tastypie-jqgrid screen](http://i.imgur.com/YKOMh.png)
![django-tastypie-jqgrid autocompletion](http://i.imgur.com/gqpyK.png)

## demo code
the code below assumes you have your models exposed to an API via TastyPie.

If you don't know what TastyPie is, here is a quick explanation:
TastyPie is a library to create REST APIs with support for Django models. 
In other words, it handles automatically serializing and deserializing your Models. 
Here, it makes the communication between Django ORM and jqGrid possible. 
Before reading the code below, read the quick [tutorial of TastyPie](http://django-tastypie.readthedocs.org/en/latest/tutorial.html)     

the code used for achieving the grid shown in the screenshot was as simple as:

``grids.py:``
```
#!python
# zero-configuration grid. Works fine for read only access.
class PostsGrid(JqGrid):
    class GridOptions:
        grid_resource = PostResource

# customized, full-featured grid        
class CustomPostsGrid(PostsGrid):
    class GridOptions:
        filtering_toolbar = True
        columns_editable_by_default = True
        pager_selector = '#gridpager'
        pager_options = {'search': False} # hidden search button
        scroll = False  # disable scrolling, we have pagination
        
        default_sort = '-date_created'
    
    id = Column(label = '#', editable = False, width = 25)    
    title = Column(label = _('Post title'), width = 230)
    author_name = AutoCompleteColumn(label = _('Author name'), width = 100,
                                     resource = UserResource(), comp_field = 'username',
                                     target_field = 'author_id')
    date_created = DateTimeColumn(label = _('Date of publication'), width = 130, 
                datepicker_edit = True, datepicker_search_tb = True)
    body = Column(label = _('Post body'), width = 430)
    
    def get_grid_options(self, user):
        return {                                
                'viewrecords': True
        }
```

``views.py``
```
#!python

class CustomPostsGridView(PostsGridView):
    template_name = "custom_config.html"
    grid = CustomPostsGrid()
```

template:
```
#!html

{% load jqgrid %}
{% block extra_head %}
	{% jqgrid_css_tags jquery_ui=True %}
    {% jqgrid_js_tags jquery_ui=True locale='pl'%}          
{% endblock %}
{% block content %}	
    <div class="wrapper">
    	<table id="my-grid"></table>
    	<div id="gridpager"></div> 
    </div>
    {% jqgrid_init "#my-grid" %}
{% endblock %}
```