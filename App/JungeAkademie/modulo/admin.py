from django.contrib import admin

# Register your models here.

from .models import Interest, Category, Module, TestPersons

admin.site.register(Interest)
admin.site.register(Category)
admin.site.register(Module)
admin.site.register(TestPersons)