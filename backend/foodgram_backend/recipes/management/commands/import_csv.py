import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from foodgram_backend.settings import BASE_DIR


class Command(BaseCommand):

    def handle(self, *args, **options):
        cur_id = 0
        filepath = os.path.join(BASE_DIR.parent.parent, 'data/') + 'ingredients.csv'
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                cur_id += 1
                Ingredient.objects.get_or_create(
                    id=cur_id,
                    name=row[0],
                    measurement_unit=row[1]
                )
