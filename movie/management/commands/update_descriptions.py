import os
from openai import OpenAI
from django.core.management.base import BaseCommand
from movie.models import Movie
from dotenv import load_dotenv

from pathlib import Path


class Command(BaseCommand):
    help = "Update movie descriptions using OpenAI API"

    def handle(self, *args, **kwargs):
        # ✅ Load environment variables from the openAI.env file located in the project root
        # Build a path relative to the project root (where manage.py lives)
        project_root = Path(__file__).resolve().parents[3]
        env_path = project_root / 'openAI.env'

        if env_path.exists():
            load_dotenv(env_path)
            self.stdout.write(f"Loaded env from: {env_path}")
        else:
            # Fallback: try default locations (do not crash here, but warn)
            load_dotenv()
            self.stdout.write(self.style.WARNING(f"openAI.env not found at {env_path}; loaded default environment variables."))

        # Prefer explicit variable name 'openai_apikey' in openAI.env
        openai_apikey = os.environ.get('openai_apikey') or os.environ.get('OPENAI_API_KEY')

        if not openai_apikey:
            self.stderr.write(self.style.ERROR('OpenAI API key not found. Please create openAI.env with openai_apikey=sk-... or set OPENAI_API_KEY in environment.'))
            return

        # Initialize the OpenAI client with the API key
        client = OpenAI(api_key=openai_apikey)

        # ✅ Helper function to send prompt and get completion from OpenAI
        def get_completion(prompt, model="gpt-3.5-turbo"):
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,  # No creativity, deterministic response
            )
            return response.choices[0].message.content.strip()

        # ✅ Instruction to guide the AI response (clear, concise, with genre info)
        instruction = (
            "Vas a actuar como un aficionado del cine que sabe describir de forma clara, "
            "concisa y precisa cualquier película en menos de 200 palabras. La descripción "
            "debe incluir el género de la película y cualquier información adicional que sirva "
            "para crear un sistema de recomendación."
        )

        # ✅ Fetch all movies from the database
        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies")

        # ✅ Process each movie
        for movie in movies:
            self.stdout.write(f"Processing: {movie.title}")
            try:
                # ✅ Construct the prompt combining the instruction and the current description
                prompt = (
                    f"{instruction} "
                    f"Vas a actualizar la descripción '{movie.description}' de la película '{movie.title}'."
                )

                # ✅ Optional: Log current movie data
                print(f"Title: {movie.title}")
                print(f"Original Description: {movie.description}")

                # ✅ Get the new description from the AI
                updated_description = get_completion(prompt)

                # ✅ Optional: Log AI response
                print(f"Updated Description: {updated_description}")

                # ✅ Save the new description to the database
                movie.description = updated_description
                movie.save()

                self.stdout.write(self.style.SUCCESS(
                    f"Updated: {movie.title}"))

            except Exception as e:
                self.stderr.write(f"Failed for {movie.title}: {str(e)}")

            # ✅ Remove the break to process all movies
            break  # Remove or comment this line to process all movies
