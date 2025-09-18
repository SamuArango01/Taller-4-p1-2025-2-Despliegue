import os
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie
from openai import OpenAI
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Generate and store embeddings for all movies in the database"

    def handle(self, *args, **kwargs):
        # ✅ Load OpenAI API key from moviereviews/openAI.env (same dir as manage.py)
        load_dotenv('openAI.env')
        api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('openai_apikey')
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "OpenAI API key not found. Set OPENAI_API_KEY in openAI.env or environment."
            ))
            return
        client = OpenAI(api_key=api_key)

        # ✅ Fetch all movies from the database
        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies in the database")

        def get_embedding(text):
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return np.array(response.data[0].embedding, dtype=np.float32)

        # ✅ Iterate through movies and generate embeddings
        for movie in movies:
            try:
                emb = get_embedding(movie.description)
                # ✅ Store embedding as binary in the database
                movie.emb = emb.tobytes()
                movie.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Embedding stored for: {movie.title}"))
            except Exception as e:
                self.stderr.write(f"❌ Failed to generate embedding for {movie.title}: {e}")

        self.stdout.write(self.style.SUCCESS("🎯 Finished generating embeddings for all movies"))