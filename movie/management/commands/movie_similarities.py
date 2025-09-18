import os
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie
from openai import OpenAI
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Compare two movies and optionally a prompt using OpenAI embeddings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--movie1",
            type=str,
            default="Avengers",
            help="Título de la primera película (por defecto: 'Avengers')",
        )
        parser.add_argument(
            "--movie2",
            type=str,
            default="Toy Story",
            help="Título de la segunda película (por defecto: 'Toy Story')",
        )
        parser.add_argument(
            "--prompt",
            type=str,
            default="película sobre superhéroes",
            help="Prompt opcional para comparar contra ambas películas",
        )

    def handle(self, *args, **kwargs):
        # Load OpenAI API key from moviereviews/openAI.env (same dir as manage.py)
        load_dotenv('openAI.env')
        api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('openai_apikey')
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "OpenAI API key not found. Set OPENAI_API_KEY in openAI.env or environment."
            ))
            return
        client = OpenAI(api_key=api_key)

        # Get parameters
        title1: str = kwargs.get("movie1")
        title2: str = kwargs.get("movie2")
        user_prompt: str = kwargs.get("prompt")

        # Fetch movies (case-insensitive lookup)
        try:
            movie1 = Movie.objects.get(title__iexact=title1)
        except Movie.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"No se encontró la película: {title1}"))
            return
        try:
            movie2 = Movie.objects.get(title__iexact=title2)
        except Movie.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"No se encontró la película: {title2}"))
            return

        def get_embedding(text):
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return np.array(response.data[0].embedding, dtype=np.float32)

        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        # Generate embeddings of both movies
        emb1 = get_embedding(movie1.description)
        emb2 = get_embedding(movie2.description)

        # Compute similarity between movies
        similarity = cosine_similarity(emb1, emb2)
        self.stdout.write(f"\U0001F3AC Similaridad entre '{movie1.title}' y '{movie2.title}': {similarity:.4f}")

        # Optional: Compare against a prompt
        prompt_emb = get_embedding(user_prompt)

        sim_prompt_movie1 = cosine_similarity(prompt_emb, emb1)
        sim_prompt_movie2 = cosine_similarity(prompt_emb, emb2)

        self.stdout.write(f"\U0001F4DD Similitud prompt ('{user_prompt}') vs '{movie1.title}': {sim_prompt_movie1:.4f}")
        self.stdout.write(f"\U0001F4DD Similitud prompt ('{user_prompt}') vs '{movie2.title}': {sim_prompt_movie2:.4f}")