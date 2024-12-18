import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShortURL, Tag)
from users.models import Follow, User


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
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj: User) -> bool:
        if (self.context.get('request')
           and not self.context['request'].user.is_anonymous):
            return Follow.objects.filter(
                user=self.context['request'].user,
                author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {
                'required': True,
                'write_only': True,
                'allow_blank': False
            },
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserTokenSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ('username', 'password')


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data.get('current_password')):
            raise serializers.ValidationError(
                "Пароль не соответсвует текущему.")
        return data


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {
                'required': True},
        }


class FollowSerializer(UserDetailSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count', 'avatar')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeBriefInfoSerializer(
            recipes,
            many=True,
            read_only=True)
        return serializer.data


class FollowAddSerializer(FollowSerializer):

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count', 'avatar')
        read_only_fields = ('email', 'username', 'avatar')

    def validate(self, obj):
        if (self.context['request'].user == obj):
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя'})
        return obj


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


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeDetailSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('author', 'tags',)

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
    ingredients = IngredientInRecipeCreateSerializer(
        many=True, source='recipe_ingredient')
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
        fields = ('ingredients', 'author',
                  'tags', 'image', 'name',
                  'text', 'cooking_time',)
        read_only_fields = ('author',)
        extra_kwargs = {
            'ingredients': {'required': True, 'allow_blank': False},
            'name': {'required': True, 'allow_blank': False},
            'text': {'required': True, 'allow_blank': False},
            'image': {'required': True, },
            'cooking_time': {'required': True, },
        }

    def validate(self, data):
        tags = data.get('tags', [])
        if len(tags) == 0:
            raise serializers.ValidationError('Выберите хотя бы 1 тег')

        if len(set(tags)) != len(tags):
            raise serializers.ValidationError('Теги должны быть уникальные')

        ingredients = data.get('recipe_ingredient', [])
        print(ingredients)
        if len(ingredients) == 0:
            raise serializers.ValidationError('Добавьте хотя бы 1 ингредиент')

        unique = len(set([item['ingredient'] for item in ingredients]))
        if (len(ingredients) != unique):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться')

        return data

    def create(self, validated_data):
        print(validated_data)
        image = validated_data.pop('image')
        tags_data = validated_data.pop('tags')

        ingredients_data = validated_data.pop('recipe_ingredient')
        recipe = Recipe.objects.create(image=image, **validated_data)

        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient.get('ingredient'),
                amount=ingredient.get("amount"),
            )

        recipe.tags.set(tags_data)
        return recipe

    def update(self, recipe, validated_data):
        if 'recipe_ingredients' in self.initial_data:
            ingredients_data = validated_data.pop('recipe_ingredients')
            recipe.ingredients.clear()
            for ingredient in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient.get('ingredient'),
                    amount=ingredient.get('amount'),
                )
        if 'tags' in self.initial_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.clear()
            recipe.tags.set(tags_data)
        recipe.save()
        return recipe

    def to_representation(self, instance):
        return RecipeDetailSerializer(instance, context=self.context).data


class RecipeBriefInfoSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooking_time')
        read_only_fields = fields


class ShortURLSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShortURL
        exclude = ()
