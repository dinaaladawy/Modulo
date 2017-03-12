from django.db import models

# Create your models here.

class Interests(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)

class Module(models.Model):
    #title, prof, time, place (F, G, H, I), exam, credits, categoryList (5 elem) -> Many-to-many relationship
    EXAM_TYPES = (('w', 'Written exam'), ('o', 'Oral exam'), ('p', 'paper'))
    LOCATIONS = (('F', 'Freising'), ('G', 'Garching'), ('H', 'Garching-Hochbrück'), ('I', 'Innenstadt'))
          
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, default='')
    description = models.TextField(editable=False, default='Empty description..')
    time = models.TimeField(default='00:00')
    place = models.CharField(max_length=1, choices=LOCATIONS, default=None)
    credit = models.IntegerField(default=0)
    exam = models.CharField(max_length=1, choices=EXAM_TYPES, default='w')
    categories = models.ManyToManyField(Category)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title', 'credit', 'time', 'id',)

class TestPersons(models.Model):
    #name, personality type (pers_type), modules
    PERSONALITY_TYPES = (('', 'strict'), ('', 'loose'), ('', 'curious'), ('', 'credit-oriented'), ('', 'lazy'), ('', 'nerd'), ('', 'do-it-all'), ('', 'time-pressured'), ('', 'detail-oriented'), ('', 'anything works'), ('', 'easy exam'), ('', 'only written exam'), ('', 'the harder, the better'), )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default='')
    pers_type = models.CharField(max_length=5, choices=PERSONALITY_TYPES, default=None)
    modules = models.ManyToManyField(Module)
    
    def __str__(self):
        return self.name + " " + self.pers_type

    class Meta:
        ordering = ('pers_type', 'name',)