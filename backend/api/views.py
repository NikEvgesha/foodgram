import hashlib, pathlib

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse

from rest_framework import status, mixins, viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Ingredient, Tag, Recipe, ShortURL
from users.models import User, Follow
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeDetailSerializer,
    RecipeCreateSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    SetPasswordSerializer,
    UserAvatarSerializer,
    ShortURLSerializer)
from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPaginator
from api.permissions import IsAuthorOrReadOnly


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




class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, ) # IsAdminOrReadOnly
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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    http_method_names = ['get', 'post', 'patch', 'delete']
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
        original_url = str(pathlib.Path(request.get_full_path()).parent)
        hash_value = hashlib.md5(original_url.encode()).hexdigest()[:16]
        short_url = f'{request.scheme}://{request.get_host()}/url/{hash_value}/'
        url = ShortURL.objects.create(short_url=hash_value, original_url=original_url)
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
def RedirectURL(request, hash):
    try:
        url = ShortURL.objects.get(short_url=hash)
        print('URL FOUND: ', url.original_url)
        serializer = ShortURLSerializer(url)
        return redirect(f'{request.scheme}://{request.get_host()}{url.original_url}')
    except ShortURL.DoesNotExist:
        return Response({'error': 'Short URL not found'}, status=status.HTTP_404_NOT_FOUND)
