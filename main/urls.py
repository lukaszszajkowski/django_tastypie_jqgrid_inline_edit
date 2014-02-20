from django.conf.urls import patterns, include, url

from main import  views

urlpatterns = patterns('main.views',
    url(r'^$', 'index', name='index'),

    url(r'^toolbargrid$', views.CustomPensionerGridView.as_view() , name='cust-colmodel'),
    url(r'^basicgrid', views.PensionerGridView.as_view() , name='auto-colmodel'),
    url(r'^inlineeditgrid$', views.InlineEditPensionerGridView.as_view() , name='inline-edit'),

    url(r'^apilist/$', 'apilist', name='apilist'),

    url(r'^(?P<reference>\d+)/$', 'detail', name='detail'),
    url(r'^(?P<reference>\d+)/edit/$', 'edit', name='detail_edit'),
)

