from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Ingredient, Tag, Recipe
from users.models import User, Follow
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeDetailSerializer,
    RecipeCreateSerializer,
    UserDetailSerializer,
    UserCreateSerializer)
from api.filters import IngredientFilter
from api.pagination import CustomPaginator


class UserDetailViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserDetailSerializer
        return UserCreateSerializer
    
    



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
    serializer_class = RecipeDetailSerializer
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']


    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeDetailSerializer
        return RecipeCreateSerializer
