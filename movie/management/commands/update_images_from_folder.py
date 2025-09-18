import os
from typing import List
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from movie.models import Movie


class Command(BaseCommand):
    help = "Asigna imágenes desde media/movie/images/ a cada película y actualiza el campo image en la base de datos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué se actualizaría sin guardar cambios en la base de datos.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # Carpetas base detectadas en tu proyecto (ambas existen con imágenes)
        # Prioridad: movies/images (más completo), luego movie/images
        search_dirs = [
            os.path.join(settings.MEDIA_ROOT, "movies", "images"),
            os.path.join(settings.MEDIA_ROOT, "movie", "images"),
        ]

        any_dir_exists = any(os.path.isdir(d) for d in search_dirs)
        if not any_dir_exists:
            self.stderr.write(
                self.style.ERROR(
                    "No existen carpetas de imágenes. Crea media/movies/images o media/movie/images."
                )
            )
            return

        movies = Movie.objects.all()
        total = movies.count()
        updated = 0
        not_found = 0
        skipped_same = 0

        self.stdout.write("Buscando imágenes en:")
        for d in search_dirs:
            self.stdout.write(f" - {d} {'(no existe)' if not os.path.isdir(d) else ''}")

        self.stdout.write(f"Películas encontradas en BD: {total}")
        self.stdout.write(f"{'(DRY RUN) ' if dry_run else ''}Iniciando asignación...")

        for movie in movies:
            candidates = self._candidate_filenames(movie.title)
            found_path = None

            # Buscar en orden en todos los directorios configurados
            for fname in candidates:
                for base_dir in search_dirs:
                    if not os.path.isdir(base_dir):
                        continue
                    full_path = os.path.join(base_dir, fname)
                    if os.path.isfile(full_path):
                        # Ignorar archivos de tamaño 0
                        try:
                            if os.path.getsize(full_path) == 0:
                                continue
                        except OSError:
                            continue
                        found_path = full_path
                        break
                if found_path:
                    break

            # Fallback: búsqueda difusa por coincidencia parcial de nombre
            if not found_path:
                raw_lower = movie.title.lower()
                slug = slugify(movie.title)
                variants = set()
                variants.add(slug)
                variants.add(slug.replace('-', '_'))
                variants.add(slug.replace('-', ''))
                # Variante con espacios sustituidos por guiones bajos (sin eliminar acentos)
                variants.add(raw_lower.replace(' ', '_'))
                # Variante sin signos de puntuación básicos
                simple = ''.join(ch if ch.isalnum() or ch in [' ', '_', '-'] else ' ' for ch in raw_lower)
                simple = '_'.join(simple.split())
                variants.add(simple)

                for base_dir in search_dirs:
                    if not os.path.isdir(base_dir):
                        continue
                    try:
                        for fname in os.listdir(base_dir):
                            fl = fname.lower()
                            # Evitar archivos de 0 bytes
                            full_path = os.path.join(base_dir, fname)
                            try:
                                if not os.path.isfile(full_path) or os.path.getsize(full_path) == 0:
                                    continue
                            except OSError:
                                continue

                            # Coincidencia si alguna variante aparece en el nombre del archivo
                            if any(v and v in fl for v in variants):
                                found_path = full_path
                                break
                        if found_path:
                            break
                    except FileNotFoundError:
                        continue

            if not found_path:
                not_found += 1
                self.stderr.write(self.style.WARNING(f"No se encontró imagen para: {movie.title}"))
                continue

            # Construir ruta relativa para guardar en el ImageField
            # Debe coincidir con upload_to='movies/images/' del modelo Movie.image
            rel_path = os.path.join("movies", "images", os.path.basename(found_path)).replace("\\", "/")

            if str(movie.image) == rel_path:
                skipped_same += 1
                self.stdout.write(f"Ya asignada: {movie.title} -> {rel_path}")
                continue

            if dry_run:
                self.stdout.write(self.style.WARNING(f"(DRY RUN) {movie.title} -> {rel_path}"))
            else:
                movie.image = rel_path
                movie.save(update_fields=["image"])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Actualizado: {movie.title} -> {rel_path}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Proceso finalizado"))
        self.stdout.write(f"Total películas: {total}")
        self.stdout.write(f"Actualizadas: {updated}")
        self.stdout.write(f"Sin cambios (ya iguales): {skipped_same}")
        self.stdout.write(f"Sin imagen encontrada: {not_found}")

    def _candidate_filenames(self, title: str) -> List[str]:
        """
        Genera posibles nombres de archivo en distintos formatos para cubrir casos comunes:
        - Con y sin prefijo 'm_'
        - Con título original y con slug
        - Extensiones: .png, .jpg, .jpeg, .webp
        """
        exts = ["png", "jpg", "jpeg", "webp"]
        raw = title  # usar el título tal cual (con espacios y signos), según tus archivos
        slug = slugify(title)

        candidates: List[str] = []

        # Observado: la mayoría están como m_<Title>.png (con espacios tal cual)
        # 1) Exacto con prefijo 'm_'
        for ext in exts:
            candidates.append(f"m_{raw}.{ext}")

        # 2) Exacto sin prefijo
        for ext in exts:
            candidates.append(f"{raw}.{ext}")

        # 3) Slug con prefijo 'm_'
        for ext in exts:
            candidates.append(f"m_{slug}.{ext}")

        # 4) Slug sin prefijo
        for ext in exts:
            candidates.append(f"{slug}.{ext}")

        # 5) Variaciones comunes: reemplazar caracteres problemáticos por guion bajo
        #    (algunos archivos pueden venir con nombres simplificados)
        simplified = (
            raw.replace("/", "_")
               .replace("\\", "_")
               .replace(":", "_")
               .replace("?", "_")
        )
        if simplified != raw:
            for ext in exts:
                candidates.append(f"m_{simplified}.{ext}")
                candidates.append(f"{simplified}.{ext}")

        return candidates