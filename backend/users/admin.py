from django.contrib import admin

from users.models import User, Follow


class UserAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email')


admin.site.register(User)
admin.site.register(Follow)
