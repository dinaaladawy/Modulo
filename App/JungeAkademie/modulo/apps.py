from django.apps import AppConfig

already_initialized = False


class ModuloConfig(AppConfig):
    name = 'modulo'
    verbose_name = 'TUM:JungeAkademie - Modulo'

    def ready(self):
        global already_initialized
        if not already_initialized:
            # start-up / initialization code here!!!
            from .algorithms import LinearClassifier
            from .filters import get_item
            from .recommender import Recommender
            from .views import initialize as views_initialize

            Recommender.initialize()
            num_interests = len(Recommender.interest_names)
            num_categories = len(Recommender.category_names)
            algorithm = LinearClassifier(num_interests=num_interests, num_categories=num_categories)
            Recommender.algorithm = algorithm

            views_initialize()
            already_initialized = True
