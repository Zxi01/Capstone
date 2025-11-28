from django.contrib import admin
from .models import Publisher


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ("name",)
    prepopulated_fields = {'slug': ('name',)}

# Register your models here.
