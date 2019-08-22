from django.views import View
from django.shortcuts import render
from django.template.loader import render_to_string
from django.forms import BaseFormSet, BaseInlineFormSet
from copy import deepcopy, copy
from importlib import import_module

class ModularView(View):
    url = None # (url, name)
    title = 'DavisMill'
    modules = [
        
    ]

    def __init__(self, *args, **kwargs):
        super(ModularView, self).__init__(*args, **kwargs)
        self.template_context = {'view': self}

    def handle_modules(self, request, method, modules, *args, **kwargs): # helper method to run all modules for a given method
        for module in modules:
            print(module, method, request.method)
            result = getattr(module, method)(request, self, *args, **kwargs)
            if result:
                return result

    def dispatch(self, request, *args, **kwargs):
        result = self.handle_modules(request, 'dispatch', self.modules, *args, **kwargs)
        if result:
            return result
        return super(ModularView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        result = self.handle_modules(request, 'get', self.modules, *args, **kwargs)
        return result

    def post(self, request, *args, **kwargs):
        result = self.handle_modules(request, 'post', self.modules, *args, **kwargs)
        return result

    def delete(self, request, *args, **kwargs):
        result = self.handle_modules(request, 'delete', self.modules, *args, **kwargs)
        return result

    def put(self, request, *args, **kwargs):
        result = self.handle_modules(request, 'put', self.modules, *args, **kwargs)
        return result

    @staticmethod
    def factory(modules, title='DavisMill'):
        """ this should be capable of creating a modular view directly in a urls.py File """
        return type('ModuleView', (ModularView,), {'modules': modules}).as_view()