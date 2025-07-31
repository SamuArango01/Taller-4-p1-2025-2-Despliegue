from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie

# Create your views here.


def home(request):
    searchTerm = request.GET.get('searchmovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm': searchTerm, 'movies': movies})


def about(request):
    return HttpResponse('<h1>About Movie Reviews</h1><p>This is a project to review movies.</p>')
