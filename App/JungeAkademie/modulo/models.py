from django.db import models
import sys, json

# Create your models here.

class Exam(models.Model):
    #WRITTEN_EXAM = 'Written exam'
    #ORAL_EXAM = 'Oral exam'
    #OTHER = 'Other'
    NOT_SPECIFIED = 'Not specified'
    exam_type = models.CharField(primary_key=True, max_length=100, default=NOT_SPECIFIED)
    
    def __str__(self):
        return self.exam_type
    
class CourseFormat(models.Model):
    #SEMINAR = 'Seminar'
    #WORKSHOP = 'Workshop'
    #COLLOQUIUM = 'Colloquium'
    #MODULE = 'Module'
    #COURSE = 'Course'
    #EXERCICE = 'Exercice'
    #EXCURSION = 'Excursion'
    #PRESENTATION = 'Presentation'
    #OTHER = 'Other'
    NOT_SPECIFIED = 'Not specified'
    course_format = models.CharField(primary_key=True, max_length=100, default=NOT_SPECIFIED)
    
    def __str__(self):
        return self.course_format
    
class Language(models.Model):
    #ENGLISH = 'English'
    #GERMAN = 'German'
    #OTHER = 'Other'
    NOT_SPECIFIED = 'Not specified'
    language = models.CharField(primary_key=True, max_length=100, default=NOT_SPECIFIED)
    
    def __str__(self):
        return self.language

class Location(models.Model):
    #FREISING = 'Freising'
    #GARCHING = 'Garching'
    #GARCHING_HOCHBRÜCK = 'Garching-Hockbrück'
    #INNER_CITY = 'Inner city'
    #OTHER = 'Other'
    NOT_SPECIFIED = 'Not specified'
    location = models.CharField(primary_key=True, max_length=500, default=NOT_SPECIFIED)
    
    def __str__(self):
        return self.location

class Personality(models.Model):
    #STRICT = 'Strict'
    #LOOSE = 'Loose'
    #CURIOUS = 'Curious'
    #CREDIT_ORIENTED = 'Credit oriented'
    #LAZY = 'Lazy'
    #NERD = 'Nerd'
    #DO_IT_ALL = 'Do it all'
    #TIME_PRESSURED = 'Time pressured'
    #DETAIL_ORIENTED = 'Detail oriented'
    #ANYTHING_WORKS = 'Anything works'
    #EASY_EXAM = 'Easy exam'
    #ONLY_WRITTEN_EXAM = 'Only written exam'
    #THE_HARDER_THE_BETTER = 'The harder, the better'
    #OTHER = 'Other'
    NOT_SPECIFIED = 'Not specified'
    personality = models.CharField(primary_key=True, max_length=200, default=NOT_SPECIFIED)    
    
    def __str__(self):
        return self.personality

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)

class Interest(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='')
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)

class HandleModule(json.JSONEncoder):
     """ json.JSONEncoder extension: handle Module """
     def default(self, obj):
         if isinstance(obj, Module) or all([isinstance(m, Module) for m in obj]):
             return Module.get_json_from_modules(obj)
         return json.JSONEncoder.default(self, obj)

class Module(models.Model):
    #title, prof, time, place (F, G, H, I), exam, credits, categoryList (5 elem) -> Many-to-many relationship
    #pk = title, language, exam, credits, place?
    
    id =            models.AutoField(primary_key=True)
    title =         models.CharField(max_length=100, default='')
    time =          models.TimeField(default='00:00')
    credits =       models.IntegerField(default=0)
    #place =         models.IntegerField(choices=LOCATIONS, default=Location.NOT_SPECIFIED)
    location =      models.ForeignKey(Location, blank=True, null=True, on_delete=models.CASCADE)
    #exam =          models.IntegerField(choices=EXAM_TYPES, default=Exam.NOT_SPECIFIED)
    exam =          models.ForeignKey(Exam, blank=True, null=True, on_delete=models.CASCADE)
    categories =    models.ManyToManyField(Category)
    
    selections =    models.BigIntegerField(default=0)
    
    # extra information about courses
    organisers =        models.TextField(editable=False, default='')
    subtitle =          models.TextField(editable=False, default='')
    description =       models.TextField(editable=False, default='')
    goals =             models.TextField(editable=False, default='')
    methods =           models.TextField(editable=False, default='')
    exam_details =      models.TextField(editable=False, default='')
    sws =               models.FloatField(default=0.0)
    minParticipants =   models.IntegerField(default=0)
    maxParticipants =   models.IntegerField(default=sys.maxsize)
    #type =              models.IntegerField(choices=COURSE_TYPES, default=CourseFormat.NOT_SPECIFIED)
    type =              models.ForeignKey(CourseFormat, null=True, on_delete=models.CASCADE)
    #language =          models.CharField(max_length=2, choices=LANGUAGES, default=Language.NOT_SPECIFIED)
    language =          models.ForeignKey(Language, null=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title

    def __eq__(self, other):
        d1 = self.__dict__
        d2 = other.__dict__
        if len(d1) != len(d2):
            return False
        for key, value in d1.items():
            if not (key.startswith('_') or (key in d2 and d2[key] == value)):
                return False
        for key, value in d2.items():
            if not (key.startswith('_') or (key in d1 and d1[key] == value)):
                return False
        return True
    
    def __ne__(self, other):
        return not self == other
    
    def module_details(self):
        return "More details on module %s coming soon to a web browser near you..." % self.title
    
    def get_json_from_modules(module):
        json_object = None
        if isinstance(module, Module):
            json_object = module.id
        elif isinstance(module, list):
            json_object = [m.id for m in module]
        else:
            raise Exception("Unknown type for module:", module)
        return json_object
    
    def get_modules_from_json(json_object):
        cleanup_json_object = json.loads(json_object)
        if isinstance(cleanup_json_object, int):
            return Module.objects.get(id=cleanup_json_object)
        elif isinstance(cleanup_json_object, list):
            return [Module.objects.get(id=m_id) for m_id in cleanup_json_object]
        else:
            raise Exception("Unknown type for json_object:", json_object)

    class Meta:
        ordering = ('title', 'credits', 'time', 'id',)

class TestPerson(models.Model):
    #name, personality type (pers_type), modules
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default='')
    #personality = models.IntegerField(choices=PERSONALITY_TYPES, default=None)
    personality = models.ForeignKey(Personality, on_delete=models.CASCADE)
    modules = models.ManyToManyField(Module)
    categories = models.ManyToManyField(Category)
    
    def __str__(self):
        return self.name + " is " + self.PERSONALITY_TYPES[self.personality][1]

    class Meta:
        ordering = ('personality', 'name',)