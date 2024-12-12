import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import Ingredient, Recipe, Tag, RecipeIngredient, Favorite, Cart
from users.models import User, Follow


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
    


''' Users app '''

class UserDetailSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField(read_only=True)
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj: User) -> bool:
        current_user = self.context.get('request').user
        if current_user.is_anonymous:
            return False
        return False  #  Follow.objects.filter(user=current_user, author=obj).exists()
    

class UserCreateSerializer(serializers.ModelSerializer):
     class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        }


''' Recipes app '''

class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name',
                  'measurement_unit', 'amount')



class RecipeDetailSerializer(serializers.ModelSerializer):
    """[GET] Список рецептов."""
    author = serializers.SlugRelatedField(slug_field='username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Cart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )
    

class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_empty=False
    )

    author = UserDetailSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients',
                'tags', 'image', 'name',
                'text', 'cooking_time',)






