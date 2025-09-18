import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Muestra el embedding de una película (aleatoria o por título)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--title",
            type=str,
            help="Título exacto (case-insensitive) de la película a inspeccionar. Si no se proporciona, se elige una al azar con embedding disponible.",
        )
        parser.add_argument(
            "--head",
            type=int,
            default=16,
            help="Cantidad de valores iniciales del embedding a mostrar (por defecto: 16).",
        )

    def handle(self, *args, **options):
        title = options.get("title")
        head = max(1, int(options.get("head") or 16))

        # No podemos filtrar por 'emb' si el modelo no define ese campo en ORM.
        # Seleccionamos la película y luego verificamos que tenga 'emb' con datos.

        if title:
            movie = Movie.objects.filter(title__iexact=title).first()
            if not movie:
                self.stderr.write(self.style.ERROR(f"No se encontró la película: {title}"))
                return
            if not hasattr(movie, 'emb') or not movie.emb:
                self.stderr.write(self.style.ERROR(f"La película '{movie.title}' no tiene embedding almacenado. Ejecuta 'python manage.py movie_embeddings' primero."))
                return
        else:
            # Buscar aleatoriamente alguna película que tenga atributo 'emb' con datos
            movie = None
            for cand in Movie.objects.order_by('?')[:50]:  # probar hasta 50 aleatorias
                if hasattr(cand, 'emb') and cand.emb:
                    movie = cand
                    break
            if not movie:
                self.stderr.write(self.style.ERROR("No hay películas con embeddings almacenados. Ejecuta 'python manage.py movie_embeddings' primero."))
                return

        # Reconstruir el vector desde bytes
        try:
            emb = np.frombuffer(movie.emb, dtype=np.float32)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"No se pudo reconstruir el embedding para '{movie.title}': {e}"))
            return

        dim = emb.shape[0]
        snippet = emb[:head]

        self.stdout.write(self.style.SUCCESS(f"Película: {movie.title}"))
        self.stdout.write(f"Dimensión del embedding: {dim}")
        self.stdout.write(f"Primeros {min(head, dim)} valores:")
        self.stdout.write("[" + ", ".join(f"{v:.6f}" for v in snippet) + ("]" if head >= dim else ", ...]") )
