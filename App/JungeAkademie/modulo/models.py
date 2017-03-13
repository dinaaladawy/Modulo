from django.db import models

# Create your models here.

class Exam():
    WRITTEN_EXAM = 0
    ORAL_EXAM = 1
    PAPER = 2
    EITHER = -1
    
class Location():
    FREISING = 0
    GARCHING = 1
    GARCHING_HOCHBRÜCK = 2
    INNER_CITY = 3
    EITHER = -1

class Personality():
    STRICT = 0
    LOOSE = 1
    CURIOUS = 2
    CREDIT_ORIENTED = 3
    LAZY = 4
    NERD = 5
    DO_IT_ALL = 6
    TIME_PRESSURED = 7
    DETAIL_ORIENTED = 8
    ANYTHING_WORKS = 9
    EASY_EXAM = 10
    ONLY_WRITTEN_EXAM = 11
    THE_HARDER_THE_BETTER = 12

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
    EXAM_TYPES = ((Exam.WRITTEN_EXAM, 'Written exam'), (Exam.ORAL_EXAM, 'Oral exam'), (Exam.PAPER, 'paper'))
    LOCATIONS = ((Location.FREISING, 'Freising'), (Location.GARCHING, 'Garching'), (Location.GARCHING_HOCHBRÜCK, 'Garching-Hochbrück'), (Location.INNER_CITY, 'Inner city'))
          
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, default='')
    description = models.TextField(editable=False, default='Empty description..')
    time = models.TimeField(default='00:00')
    place = models.IntegerField(choices=LOCATIONS, default=None)
    credit = models.IntegerField(default=0)
    exam = models.IntegerField(choices=EXAM_TYPES, default=Exam.WRITTEN_EXAM)
    categories = models.ManyToManyField(Category)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title', 'credit', 'time', 'id',)

class TestPersons(models.Model):
    #name, personality type (pers_type), modules
    PERSONALITY_TYPES = ((Personality.STRICT, 'strict'), (Personality.LOOSE, 'loose'), (Personality.CURIOUS, 'curious'), (Personality.CREDIT_ORIENTED, 'credit-oriented'), (Personality.LAZY, 'lazy'), (Personality.NERD, 'nerd'), (Personality.DO_IT_ALL, 'do-it-all'), (Personality.TIME_PRESSURED, 'time-pressured'), (Personality.DETAIL_ORIENTED, 'detail-oriented'), (Personality.ANYTHING_WORKS, 'anything works'), (Personality.EASY_EXAM, 'easy exam'), (Personality.ONLY_WRITTEN_EXAM, 'only written exam'), (Personality.THE_HARDER_THE_BETTER, 'the harder, the better'), )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default='')
    pers_type = models.IntegerField(choices=PERSONALITY_TYPES, default=None)
    modules = models.ManyToManyField(Module)
    
    def __str__(self):
        return self.name + " is " + self.PERSONALITY_TYPES[self.pers_type][1]

    class Meta:
        ordering = ('pers_type', 'name',)