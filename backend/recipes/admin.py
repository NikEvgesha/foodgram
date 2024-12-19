from django.contrib import admin

from recipes.models import Ingredient, Recipe, ShortURL, Tag, Cart, Favorite


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'in_favorites')
    list_filter = ('name', 'author', 'tags')

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorites.count()


admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(ShortURL)
admin.site.register(Cart)
admin.site.register(Favorite)
