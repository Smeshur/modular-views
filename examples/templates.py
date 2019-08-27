from view import *
from modules import *

class BasicTemplateView(ModularView):
    modules = [
        # by default, 
        RenderTemplate('')
    ]