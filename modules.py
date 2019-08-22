from django.shortcuts import render
from django.template.loader import render_to_string
from django.forms import BaseFormSet, BaseInlineFormSet
from copy import deepcopy, copy
from importlib import import_module
import re

def raw(val):
    """ Used to return a raw value to callback parameters"""
    return lambda *a,**k: val


class ViewModule(object):
    """
        a view module contains logic for a specific part of a view
        ex. Form, Load Model, Etc.
    """

    def get(self, request, view, *args, **kwargs):
        pass

    def post(self, request, view, *args, **kwargs):
        pass

    def delete(self, request, view, *args, **kwargs):
        pass

    def put(self, request, view, *args, **kwargs):
        pass

    def dispatch(self, request, view, *args, **kwargs):
        pass

    def lookup_value(self, request, view, val, *args, **kwargs):
        """
            looks for a url or query parameter with the given name
        """
        if callable(val):
            return val(request, view)

        return kwargs.get(val, None) or request.GET.get(val, None) or request.POST.get(val, None)

    def process_callback(self, request, view, value, *args, **kwargs):
        if callable(value) and not isinstance(value, type):
            return value(request, view, *args, **kwargs)
        elif isinstance(value, type):
            return value
        elif value:
            lookup_locations = [view, self]
            if hasattr(self, 'callback_locations'):
                lookup_locations += self.callback_locations
            for src in lookup_locations:
                attr = getattr(src, value)

                if callable(attr):
                    return attr(request, view, *args, **kwargs) if hasattr(src, value) else None
                else:
                    return attr
                


class LoadModel(ViewModule):
    """ Loads single model """

    def __init__(self, Model, name=None, lookup_parameters={}, on_delete=None, after_load=None, *args, **kwargs):
        self.Model = Model
        self.name = name or Model.__name__
        self.lookup_parameters = lookup_parameters
        self.delete_endpoint = on_delete
        self.after_load = after_load

    def get_lookup(self, request, view, *args, **kwargs):
        # return default lookup dictionary for object using lookup_parameters first check url, then 
        return { k: self.lookup_value(request, view, v, *args, **kwargs) for k,v in self.lookup_parameters.iteritems() }

    def load_object(self, request, view, *args, **kwargs):
        # we only want to return an object if the lookup_parameters permit
        Model = self.process_callback(request, view, self.Model, *args, **kwargs)

        if self.lookup_parameters and len(self.lookup_parameters) > 0:
            try:    # using errors to control the flow of the application is bad
                return Model.objects.get(**self.get_lookup(request, view, *args, **kwargs)) # returns object based on query parameters
            except Exception as e:
                print(e)
        return Model()     # otherwise, create an unsaved instance of the model

    def dispatch(self, request, view, *args, **kwargs):
        if not hasattr(view, 'models'): # create model container if it doesn't exist
            view.models = {}
        # Append Model Result
        view.models[self.name] = self.load_object(request, view, *args, **kwargs)
        view.template_context[self.name] = view.models[self.name]
        if self.after_load:
            if callable(self.after_load):
                return self.after_load(request, view, view.models[self.name])
            else:
                return getattr(view, self.after_load)(request, view, view.models[self.name], *args, **kwargs)

    def delete(self, request, view, *args, **kwargs):
        if self.delete_endpoint:
            view.models[self.name].delete()
            return self.process_callback(request, view, self.delete_endpoint, *args, **kwargs)

class LoadModelList(ViewModule):
    def __init__(self, Model, name=None, filter_parameters={}, exclude_parameters={}, filter_raw={}, exclude_raw={}):
        self.Model = Model
        self.name = name or Model.__name__
        self.filter_parameters = filter_parameters
        self.filter_raw = filter_raw        
        self.exclude_parameters = exclude_parameters
        self.exclude_raw = exclude_raw

    def get_filter(self, request, view, *args, **kwargs):
        # return default filter dictionary for objects using include_parameters
        result = { k: self.lookup_value(request, view, v, *args, **kwargs) for k,v in self.filter_parameters.iteritems() }

        for k,v in self.filter_raw.iteritems():
            result[k] = v

        return result

    def get_exclude(self, request, view, *args, **kwargs):
        result = { k: self.lookup_value(request, view, v, *args, **kwargs) for k,v in self.exclude_parameters.iteritems() }

        for k,v in self.exclude_raw.iteritems():
            result[k] = v

        return result

    def load_objects(self, request, view, *args, **kwargs):
        Model = self.Model
        if not isinstance(self.Model, type):
            Model = self.Model(request, view)

        return Model.objects.filter(**self.get_filter(request, view, **kwargs)).exclude(**self.get_exclude(request, view, **kwargs))

    def dispatch(self, request, view, *args, **kwargs):
        if not hasattr(view, 'models'): # create model container if it doesn't exist
            view.models = {}
        # Append Model Result
        view.models[self.name] = self.load_objects(request, view, *args, **kwargs)
        view.template_context[self.name] = view.models[self.name]

class FilterModelList(ViewModule):
    """ filters a given  """

    def __init__(self, name, filter):
        self.name = name
        self.filter = filter

    def dispatch(self, request, view, *args, **kwargs):
        view.models[self.name] = self.process_callback(request, view, self.filter, view.models[self.name], *args, **kwargs) 
        view.template_context[self.name] = view.models[self.name]

class Breadcrumb(ViewModule):
    """ creates a breadcrumb entry """

    def __init__(self, name, url):
        self.name = name
        self.url = url

    def dispatch(self, request, view, *args, **kwargs):
        if not hasattr(view, 'breadcrumbs'):
            view.breadcrumbs = []

        if callable(self.name):
            name = self.name(view, request)
        else:
            name = self.name

        if callable(self.url):
            url = self.url(view, request)
        else:
            url = self.url

        view.breadcrumbs.append((name, url))
        view.template_context['breadcrumbs'] = view.breadcrumbs

class RenderTemplate(ViewModule):
    """ Generic template rendering module """
    def __init__(self, get_template, post_template=None):
        self.get_template = get_template
        self.post_template = post_template or get_template

    def get(self, request, view, *args, **kwargs):
        return render(request, self.get_template, view.template_context)

    def post(self, request, view, *args, **kwargs):
        return render(request, self.post_template, view.template_context)

class CallbackModule(ViewModule):
    """
        Utility module for executing arbitrary code
    """

    def __init__(self, get=None, post=None, dispatch=None, delete=None):
        # override the get, post, or dispatch method if necessary
        self._get = get
        self._post = post
        self._dispatch = dispatch
        self._delete = delete

    def get(self, request, view, *args, **kwargs):
        return self.process_callback(request, view, self._get, *args, **kwargs)

    def post(self, request, view, *args, **kwargs):
        return self.process_callback(request, view, self._post, *args, **kwargs)

    def dispatch(self, request, view, *args, **kwargs):
        return self.process_callback(request, view, self._dispatch, *args, **kwargs)

    def delete(self, request, view, *args, **kwargs):
        return self.process_callback(request, view, self._delete, *args, **kwargs)

class LoadForm(ViewModule):
    """ Handles forms and formsets """

    def __init__(self, form, name=None, model_name=None, save_success_callback=None, *args, **kwargs):
        self.FormClass = form
        self.handle_save = kwargs.pop('handle_save', True)
        self.init_args = list(args)
        self.init_kwargs = kwargs
        self.instance = model_name
        self.name = name or form.__name__
        self.callback = save_success_callback

    def post(self, request, view, *args, **kwargs):
        if view.forms[self.name].is_valid():
            if self.handle_save:
                view.forms[self.name].save()

            return self.process_callback(request, view, self.callback, *args, **kwargs)

    def dispatch(self, request, view, *args, **kwargs):
        iargs = copy(self.init_args)
        ikwargs = copy(self.init_kwargs)
        # since init is only called when view class is built, we need to copy these

        Form = self.process_callback(request, view, self.FormClass)
        self.is_formset = issubclass(Form, BaseFormSet) and not issubclass(Form, BaseInlineFormSet) # is this good enough?

        if not hasattr(view, 'forms'):
            view.forms = {}
        # this needs to change to account for formsets and forms
        if self.instance:
            instance = self.instance(view, request) if callable(self.instance) else view.models[self.instance]
            if self.is_formset:
                ikwargs['queryset'] = instance
            else:
                ikwargs['instance'] = instance

        if request.POST:
            iargs.insert(0, request.POST)
            iargs.insert(1, request.FILES)

        view.forms[self.name] = Form(*iargs, **ikwargs)
        view.template_context[self.name] = view.forms[self.name]


class RenderPartial(ViewModule):
    """ renders a section of a layout | add RenderLayout module to return rendered layout """
    def __init__(self, section, template):
        self.name = section
        self.template = template
    
    def render(self, request, view):
        if callable(self.template):
            return self.template(request, view)
        return render_to_string(self.template, view.template_context, request)

    def get(self, request, view, *args, **kwargs):
        view.layout_sections[self.name] = self.render(request, view)

    def post(self, request, view, *args, **kwargs):
        view.layout_sections[self.name] = self.render(request, view)

    def dispatch(self, request, view, *args, **kwargs):
        if not hasattr(view, 'layout_sections'): # if layout section placeholder does not exist
            view.layout_sections = {}   # create it
        


class RenderLayout(ViewModule):
    """ returns the fully rendered layout for the page | use RenderPartial modules to render parts of the page """

    def __init__(self, layout, base, layout_settings={}):
        self.layout = layout
        self.base = base
        self.layout_settings = layout_settings

    def render(self, request, view, *args, **kwargs):
        view.template_context['base'] = self.base
        return render(request, self.layout, dict(dict(view.template_context, **self.layout_settings), **view.layout_sections))

    def get(self, request, view, *args, **kwargs):
        return self.render(request, view, *args, **kwargs)

    def post(self, request, view, *args, **kwargs):
        return self.render(request, view, *args, **kwargs)

# lets make an AjaxEndpoint module that accepts a list of (url, method_name or lambda) and provides them as an ajax api
# NOTE: Changed to be (url, [modules])


class AjaxModule(ViewModule):
    """ 
        Accepts a list of (url, [modules])
        Urls can use regex, however the URL entry in urls.py will need to have a regex formula that matches all possible ajax urls.
        
        since this is attached to the same view, you have access to anything generated by view modules, thus reducing repetetive code.
    """

    def __init__(self, endpoints, *args, **kwargs):
        self.endpoints = endpoints


    def dispatch(self, request, view, *args, **kwargs): # this is kinda gross, but it's functional (READABILITY COUNTS!)
        if request.is_ajax():
            for url, modules in self.endpoints:
                sr = re.search(url, request.path)
                if sr:
                    nkwargs = dict(kwargs, **sr.groupdict())
                    result = view.handle_modules(request, 'dispatch', modules, *args, **nkwargs)
                    if result:
                        return result
                    result = view.handle_modules(request, request.method.lower(), modules, *args, **nkwargs)
                    if result:
                        return result


class ModuleContainer(ViewModule):
    modules = []

    def dispatch(self, request, view, *args, **kwargs): # this is kinda gross, but it's functional (READABILITY COUNTS!)
        result = view.handle_modules(request, 'dispatch', self.modules, *args, **kwargs)
        if result:
            return result
        result = view.handle_modules(request, request.method.lower(), self.modules, *args, **kwargs)
        if result:
            return result


class ConditionalModules(ViewModule):
    def __init__(self, condition, modules):
        self.modules = modules
        self.condition = condition

    def get(self, request, view, *args, **kwargs):
        if self._passes_condition:
            return view.handle_modules(request, 'get', self.modules, *args, **kwargs)

    def post(self, request, view, *args, **kwargs):
        if self._passes_condition:
            return view.handle_modules(request, 'post', self.modules, *args, **kwargs)

    def delete(self, request, view, *args, **kwargs):
        if self._passes_condition:
            return view.handle_modules(request, 'delete', self.modules, *args, **kwargs)

    def put(self, request, view, *args, **kwargs):
        if self._passes_condition:
            return view.handle_modules(request, 'put', self.modules, *args, **kwargs)

    def dispatch(self, request, view, *args, **kwargs):
        # cache if condition is valid
        self._passes_condition = self.process_callback(request, view, self.condition, *args, **kwargs)

        # only execute if valid
        if self._passes_condition:
            if hasattr(self, 'callback_locations') and self.callback_locations: # make sure to include the callback locations
                for module in self.modules:
                    module.callback_locations = self.callback_locations

            return view.handle_modules(request, 'dispatch', self.modules, *args, **kwargs)


class ViewProperty(ViewModule):
    def __init__(self, name, value):
       self.name = name
       self.value = value

    def dispatch(self, request, view, *args, **kwargs):
        view.template_context[self.name] = self.process_callback(request, view, self.value, *args, **kwargs)