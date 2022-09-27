from django.db import models

# Create your models here.
class Page(models.Model):
    name = models.CharField(max_length=254)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)
    visible = models.BooleanField(default=True)
    # ezzel határozzuk és válsztjuk szét hogy lawyer block
    draft = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ('-created_at', )
