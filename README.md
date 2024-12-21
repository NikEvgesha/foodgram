# Проект Foodgram
## Описание проекта
Foodgram - приложение для публикации рецептов. Пользователи имеют возможность создавать собственные рецепты, а также просматривать чужие. В качестве дополнительных возможностей предусмотрено добавление рецепта в список избранного и в корзину, а также формирование списка покупок на основе корзины. Также пользователи могут подписываться на других авторов.

приложение доступно по адресу foodgram-yp.sytes.net

## Локальное развертывание проекта
1. Склонируйте репозиторий
2. Создайте и активируйте виртуальной окружение
3. Создайте файл .env в корне проекта (пример файла см. в .env.example)
4. Выполните команду
```bash
docker-compose up -d --build
```
5. Выполните миграции:
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```
6. Создайте суперпользователя:
```bash
docker-compose exec backend python manage.py createsuperuser
```

7. Соберите статику:
```bash
docker-compose exec backend python manage.py collectstatic
```

8. Заполните базу ингредиентами:
```bash
docker-compose exec backend python manage.py import_csv

