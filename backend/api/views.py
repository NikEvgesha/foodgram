import hashlib

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPaginator
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FollowAddSerializer, FollowSerializer,
                             IngredientSerializer, RecipeBriefInfoSerializer,
                             RecipeCreateSerializer, RecipeDetailSerializer,
                             SetPasswordSerializer,
                             TagSerializer, UserAvatarSerializer,
                             UserCreateSerializer, UserDetailSerializer)
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Cart, Favorite, Ingredient, Recipe, ShortURL, Tag
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated)
from rest_framework.response import Response
from users.models import Follow, User


class UserDetailViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserDetailSerializer
    permission_classes = (AllowAny, )
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserDetailSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserCreateSerializer

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data)

        if request.method == "DELETE":
            if user.avatar:
                user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"avatar": user.avatar.url},
                        status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated, ),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(followed__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FollowSerializer(page, many=True,
                                          context={'request': request})
            return self.get_paginated_response(serializer.data)
        return Response('Нет подписок :(',
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        user = request.user
        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    'Вы уже подписаны на этого автора',
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = FollowAddSerializer(
                author,
                data=request.data,
                context={"request": request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Follow.objects.filter(
                    user=request.user,
                    author=author).exists():
                return Response(
                    'Такой подписки не существует',
                    status=status.HTTP_400_BAD_REQUEST)
            get_object_or_404(Follow, user=request.user,
                              author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeDetailSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=('GET',),
        url_path='get-link',
    )
    def get_link(self, request, pk):
        original_url = f'/recipes/{pk}'
        url = ShortURL.objects.filter(original_url=original_url)
        if (url.exists()):
            hash_value = url[0].short_url
        else:
            hash_value = hashlib.md5(original_url.encode()).hexdigest()[:16]
            ShortURL.objects.create(
                short_url=hash_value,
                original_url=original_url)
        short = f'{request.scheme}://{request.get_host()}/url/{hash_value}/'
        return Response({'short-link': short}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if (request.method == 'POST'):
            if Cart.objects.filter(user=request.user, recipe__id=pk).exists():
                return Response(
                    {'errors': 'Этот рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = get_object_or_404(Recipe, id=pk)
            Cart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeBriefInfoSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if (request.method == 'DELETE'):
            recipe = get_object_or_404(Recipe, id=pk)
            cart_obj = Cart.objects.filter(user=request.user, recipe=recipe)
            if cart_obj.exists():
                cart_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепта нет в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if (request.method == 'POST'):
            if Favorite.objects.filter(
                    user=request.user,
                    recipe__id=pk).exists():
                return Response(
                    {'errors': 'Этот рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = get_object_or_404(Recipe, id=pk)
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeBriefInfoSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if (request.method == 'DELETE'):
            recipe = get_object_or_404(Recipe, id=pk)
            fav_obj = Favorite.objects.filter(user=request.user, recipe=recipe)
            if fav_obj.exists():
                fav_obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепта нет в списке избранного'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        print("user id: ", user.id)
        query = f'''
        SELECT 1 as id,
            recipes_ingredient.name as name,
            SUM(recipes_recipeingredient.amount) as amount,
            recipes_ingredient.measurement_unit as measure
            FROM recipes_cart
            INNER JOIN recipes_recipe on recipe_id = recipes_recipe.id
            JOIN recipes_recipeingredient 
            on recipes_recipe.id = recipes_recipeingredient.recipe_id
            INNER JOIN recipes_ingredient 
            on recipes_recipeingredient.ingredient_id = recipes_ingredient.id
            WHERE recipes_cart.user_id = {user.id}
            GROUP BY recipes_ingredient.name,
                recipes_ingredient.measurement_unit;
        '''

        with connection.cursor() as cursor:
            cursor.execute(query)
            ingredients = cursor.fetchall()

        content = 'Список покупок\n'
        for ingredient in ingredients:
            row = f'{ingredient[1]} - {ingredient[2]} {ingredient[3]}.\n\n'
            content += row

        response = HttpResponse(content, content_type='text/plain')
        filename = 'shopping_list.txt'
        response['Content-Disposition'] = (f'attachment; filename={filename}')

        return response


@api_view(['GET'])
def RedirectURL(request, hash):
    url = get_object_or_404(ShortURL, short_url=hash)
    return redirect(
        f'{request.scheme}://{request.get_host()}{url.original_url}')
