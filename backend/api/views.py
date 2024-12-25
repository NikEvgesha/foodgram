import hashlib

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPaginator
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FollowAddSerializer, FollowSerializer,
                             IngredientSerializer, RecipeBriefInfoSerializer,
                             RecipeCreateSerializer, RecipeDetailSerializer,
                             TagSerializer, UserAvatarSerializer)
from users.models import Follow, User
from recipes.models import (Cart, Favorite, Ingredient,
                            Recipe, ShortURL, Tag, RecipeIngredient)


class UserDetailViewSet(UserViewSet):
    pagination_class = CustomPaginator

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated, ]
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data)

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': user.avatar.url},
                        status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated, )
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
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = FollowAddSerializer(
                author,
                data=request.data,
                context={"request": request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)

        deleted_count, _ = Follow.objects.filter(
            user=request.user,
            author=author).delete()
        if deleted_count == 0:
            return Response(
                'Такой подписки не существует',
                status=status.HTTP_400_BAD_REQUEST)
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

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)

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

        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Cart.objects.filter(
            user=request.user,
            recipe=recipe).delete()
        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепта нет в корзине покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

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

        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe).delete()
        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепта нет в списке избранного'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        cart = (Cart.objects
                .filter(user=request.user)
                .values_list('recipe')
                )
        ingredients = (RecipeIngredient.objects
                       .filter(recipe_id__in=cart,)
                       .values('ingredient__name',
                               'ingredient__measurement_unit')
                       .annotate(total=Sum('amount')))

        content = 'Список покупок\n'
        for ingredient in ingredients:
            row = (f"{ingredient['ingredient__name']} - {ingredient['total']}"
                   f" {ingredient['ingredient__measurement_unit']}.\n")
            content += row

        response = HttpResponse(content, content_type='text/plain')
        filename = 'shopping_list.txt'
        response['Content-Disposition'] = (f'attachment; filename={filename}')

        return response


@api_view(['GET'])
def redirect_url(request, hash):
    url = get_object_or_404(ShortURL, short_url=hash)
    return redirect(
        f'{request.scheme}://{request.get_host()}{url.original_url}')
