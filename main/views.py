# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic.base import TemplateView
from tastypie_jqgrid.views import JqGridMixin
from .models import Pensioner
from .grids import PensionerGrid, CustomPensionerGrid, InlineEditPensionerGrid

def home(request):
    pensioner = Pensioner.objects.filter(surname="Smith")[0]
    return render(request, 'index.html', {'pensioner': pensioner})

def index(request):
    list = Pensioner.objects.all().order_by('-surname')[:5] #  List 5 members
    return render(request, 'list.html', {'list': list})

def detail(request, reference):
    pensioner = Pensioner.objects.filter(reference=reference)[0]
    return render(request, 'detail.html', {'pensioner': pensioner})

def edit(request, reference):
    pensioner = Pensioner.objects.filter(reference=reference)[0]

    if request.method == 'POST':
        pensioner.title = request.POST['title']
        pensioner.forename = request.POST['forename']
        pensioner.surname = request.POST['surname']
        pensioner.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('main.views.home'))

    return render(request, 'detail_edit.html', {'pensioner': pensioner})


def apilist(request):
    list = Pensioner.objects.all().order_by('-surname') #  List 5 members
    return render(request, 'api.html', {'list': list})

class PensionerGridView(JqGridMixin, TemplateView):
    template_name = "showgrid.html"
    grid = PensionerGrid()

class CustomPensionerGridView(PensionerGridView):
    template_name = "showgrid.html" #because we want custom description, nothing more.
    grid = CustomPensionerGrid()

class InlineEditPensionerGridView(PensionerGridView):
    template_name = "showgrid.html" #because we want custom description, nothing more.
    grid = InlineEditPensionerGrid()