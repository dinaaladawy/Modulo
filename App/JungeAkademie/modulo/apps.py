from django.apps import AppConfig


class ModuloConfig(AppConfig):
    name = 'modulo'
    verbose_name = 'TUM:JungeAkademie - Modulo'
    
    def ready(self):
        #start-up / initialization code here!!!
        from .recommender import Recommender
        Recommender.initialize()