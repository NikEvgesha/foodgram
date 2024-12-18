import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        cur_id = 0
        with open('data/ingredients.csv', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                cur_id += 1
                Ingredient.objects.get_or_create(
                    id=cur_id,
                    name=row[0],
                    measurement_unit=row[1]
                )
