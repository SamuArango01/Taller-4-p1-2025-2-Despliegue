from django.core.management.base import BaseCommand
from movie.models import Movie
import os
import json


class Command(BaseCommand):
    help = 'Load movies from movies.json into the Movie model'

    def handle(self, *args, **kwargs):
        # Construct the full path to the JSON file
        json_file_path = 'movie/management/commands/movies.json'

        # Load data from the JSON file
        with open(json_file_path, 'r') as file:
            movies = json.load(file)

        cont = 0  # Contador para llevar registro de películas agregadas

        # Add movies to the database
        for i in range(100):
            if i >= len(movies):  # Verificar que no exceda el tamaño del array
                break

            movie = movies[i]
            exist = Movie.objects.filter(title=movie['title']).first()

            if not exist:
                try:
                    Movie.objects.create(
                        title=movie['title'],
                        image='movies/images/default.jpg',  # ✅ Coincide con upload_to
                        genre=movie['genre'],
                        year=movie['year'],
                        description=movie['plot']
                    )
                    cont += 1
                    self.stdout.write(f'Agregada: {movie["title"]}')
                except Exception as e:
                    self.stdout.write(
                        f'Error al crear {movie["title"]}: {str(e)}')
            else:
                try:
                    exist.title = movie["title"]
                    exist.image = 'movies/images/default.jpg'  # ✅ Coincide con upload_to
                    exist.genre = movie["genre"]
                    exist.year = movie["year"]
                    exist.description = movie["plot"]
                    exist.save()
                    self.stdout.write(f'Actualizada: {movie["title"]}')
                except Exception as e:
                    self.stdout.write(
                        f'Error al actualizar {movie["title"]}: {str(e)}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. {cont} películas nuevas agregadas.')
        )
