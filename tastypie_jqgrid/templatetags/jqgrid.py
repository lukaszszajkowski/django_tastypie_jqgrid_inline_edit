from django import template
from django.conf import settings

register = template.Library()

JS_EXTERNAL_HEADER = '<script type="text/javascript" src="%(static)s%(path)s"></script>'
CSS_EXTERNAL_HEADER = '<link rel="stylesheet" href="%(static)s%(path)s">'
@register.simple_tag(takes_context = True)
def jqgrid_js_tags(context, jquery = False, jquery_ui = False, locale = 'en'):
    static_url = context['STATIC_URL']
    paths = []
    if jquery:
        paths.append('jqgrid/js/jquery-1.7.2.min.js')
    if jquery_ui:
        paths.append('jquery-ui/js/jquery-ui-1.9.2.custom.min.js')
    paths.append('jqgrid/js/jquery.jqGrid.%s.js' % ('src' if settings.DEBUG else 'min'))
    if not locale == False: 
        paths.append('jqgrid/js/i18n/grid.locale-%s.js' % locale)
    paths.append('mgrid/mgrid.js')
    return '\n'.join([JS_EXTERNAL_HEADER % {'path': path, 'static': static_url} for path in paths])
    

@register.simple_tag(takes_context = True)
def jqgrid_css_tags(context, jquery_ui = False):
    static_url = context['STATIC_URL']
    paths = []    
    if jquery_ui:
        paths.append('jquery-ui/css/ui-lightness/jquery-ui-1.9.2.custom.css')
    paths.append('jqgrid/css/ui.jqgrid.css')            
    
    return '\n'.join([CSS_EXTERNAL_HEADER % {'path': path, 'static': static_url} for path in paths])

@register.simple_tag(takes_context = True)
def jqgrid_init(context, selector = '#grid'):
    code = """<script type="text/javascript">
                $(function(){
                        $("%(selector)s").mGrid2(%(options)s);    
                });
                </script>""" % {
                'selector': selector,
                'options': context['grid_options_js']
            } 
    return code 