from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Tag, Recipe
from users.models import User

class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(
        method='is_favorited_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def is_favorite_filter(self, queryset, name, value):
        return self.filter_from_kwargs(queryset, value, name)

    def is_in_shopping_cart_filter(self, queryset, name, value):
        return self.filter_from_kwargs(queryset, value, name)
