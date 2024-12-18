from django.contrib import admin
from recipes.models import Ingredient, Recipe, ShortURL, Tag

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(ShortURL)
