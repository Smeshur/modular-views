from django.views import View

class ModularView(View):
    modules = [
        
    ]

    def __init__(self, *args, **kwargs):
        super(ModularView, self).__init__(*args, **kwargs)
        self.template_context = {'view': self}

    # helper method to run all modules for a given method
    def handle_modules(self, request, method, modules, *args, **kwargs): 
        for module in modules:
            result = getattr(module, method)(request, self, *args, **kwargs)
            if result:
                return result

    # dispatch does not require a response, but will return one if given
    def dispatch(self, request, *args, **kwargs):
        result = self.handle_modules(request, 'dispatch', self.modules, *args, **kwargs)
        if result:
            return result
        return super(ModularView, self).dispatch(request, *args, **kwargs)

    # get post put and delete all expect a response

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
    
    # copy of lookup_value on view object
    def lookup_value(self, request, val, *args, **kwargs):
        """
            looks for a url or query parameter with the given name
        """
        if callable(val):
            return val(request, self, *args, **kwargs)

        return kwargs.get(val, None) or request.GET.get(val, None) or request.POST.get(val, None)
