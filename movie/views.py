from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie
from django.db.models import Count
import json

# Create your views here.


def home(request):
    searchTerm = request.GET.get('searchmovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm': searchTerm, 'movies': movies})


def about(request):
    return render(request, 'about.html')


def signup(request):
    email = request.GET.get('email')
    return render(request, 'signup.html', {'email': email})


def statistics(request):
    # Obtener datos de la base de datos para estadísticas

    # 1. Películas por género
    movies_by_genre = Movie.objects.values('genre').annotate(
        count=Count('genre')
    ).order_by('-count')

    # 2. Películas por año
    movies_by_year = Movie.objects.values('year').annotate(
        count=Count('year')
    ).order_by('year')

    # 3. Total de películas
    total_movies = Movie.objects.count()

    # 4. Géneros únicos
    unique_genres = Movie.objects.values_list(
        'genre', flat=True).distinct().count()

    # 5. Años únicos
    unique_years = Movie.objects.values_list(
        'year', flat=True).distinct().count()

    # Preparar datos para gráficas (convertir a formato JSON)
    genre_labels = [item['genre'] for item in movies_by_genre]
    genre_data = [item['count'] for item in movies_by_genre]

    year_labels = [str(item['year']) for item in movies_by_year]
    year_data = [item['count'] for item in movies_by_year]

    context = {
        'total_movies': total_movies,
        'unique_genres': unique_genres,
        'unique_years': unique_years,
        'movies_by_genre': movies_by_genre,
        'movies_by_year': movies_by_year,
        'genre_labels': json.dumps(genre_labels),
        'genre_data': json.dumps(genre_data),
        'year_labels': json.dumps(year_labels),
        'year_data': json.dumps(year_data),
    }

    return render(request, 'statistics.html', context)
