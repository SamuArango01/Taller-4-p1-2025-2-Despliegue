from django.db import models

# Create your models here.


class Movie(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    image = models.ImageField(upload_to='movies/images/')  # ✅ SIN "media/"
    url = models.URLField(blank=True)
    genre = models.CharField(blank=True, max_length=250)
    year = models.IntegerField(blank=True, null=True)
    # Almacena el embedding como binario (np.float32.tobytes())
    emb = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return self.title
