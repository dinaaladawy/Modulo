from django.contrib import admin

# Register your models here.

from .models import CourseFormat, Exam, Language, Location, Personality
from .models import Interest, Category, Module, TestPerson

admin.site.register(CourseFormat)
admin.site.register(Exam)
admin.site.register(Language)
admin.site.register(Location)
admin.site.register(Personality)

admin.site.register(Interest)
admin.site.register(Category)
admin.site.register(Module)
admin.site.register(TestPerson)