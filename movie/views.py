from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def home(request):
    # return HttpResponse('<h1>Welcome to home page</h1>')
    # return render(request, 'home.html')
    return render(request, 'home.html', {'name': 'Emmanuel Cortés'})


def about(request):
    return HttpResponse('<h1>About Movie Reviews</h1><p>This is a project to review movies.</p>')
