from django.contrib import admin

from recipes.models import Tag, Ingredient, Recipe

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
