import os
import numpy as np
from django.shortcuts import render
from movie.models import Movie
from openai import OpenAI
from dotenv import load_dotenv

def _get_api_key():
    # Carga la API key desde openAI.env (junto a manage.py)
    load_dotenv('openAI.env')
    return os.environ.get('OPENAI_API_KEY') or os.environ.get('openai_apikey')

def _get_embedding(client, text: str):
    text = (text or "").replace("\n", " ")
    resp = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return np.array(resp.data[0].embedding, dtype=np.float32)

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def index(request):
    context = {"result": None, "prompt": "", "error": ""}

    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        context["prompt"] = prompt

        if not prompt:
            context["error"] = "Por favor ingresa un prompt/descripción."
            return render(request, "recommendations/index.html", context)

        api_key = _get_api_key()
        if not api_key:
            context["error"] = "No se encontró la OpenAI API key. Define OPENAI_API_KEY en openAI.env."
            return render(request, "recommendations/index.html", context)

        client = OpenAI(api_key=api_key)

        try:
            prompt_emb = _get_embedding(client, prompt)
        except Exception as e:
            context["error"] = f"Error generando embedding del prompt: {e}"
            return render(request, "recommendations/index.html", context)

        best = {"movie": None, "similarity": -1.0}
        movies = Movie.objects.all()

        for m in movies:
            emb_vec = None
            # Usar cache si el campo emb existe y tiene datos
            if hasattr(m, "emb") and m.emb:
                try:
                    emb_vec = np.frombuffer(m.emb, dtype=np.float32)
                except Exception:
                    emb_vec = None

            if emb_vec is None:
                # Calcular al vuelo y cachear si el modelo tiene ese campo
                try:
                    emb_vec = _get_embedding(client, m.description)
                    if hasattr(m, "emb"):
                        m.emb = emb_vec.tobytes()
                        m.save(update_fields=["emb"])
                except Exception:
                    continue

            sim = _cosine_similarity(prompt_emb, emb_vec)
            if sim > best["similarity"]:
                best["movie"] = m
                best["similarity"] = sim

        if best["movie"] is None:
            context["error"] = "No fue posible calcular recomendaciones."
        else:
            context["result"] = {
                "title": best["movie"].title,
                "description": best["movie"].description,
                "image_url": best["movie"].image.url if best["movie"].image else "",
                "similarity": best["similarity"],
            }

        return render(request, "recommendations/index.html", context)

    return render(request, "recommendations/index.html", context)