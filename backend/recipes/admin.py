from django.contrib import admin

from recipes.models import Tag, Ingredient, Recipe, ShortURL

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(ShortURL)
