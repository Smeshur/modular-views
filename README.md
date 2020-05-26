# modular-views
Modular Class based Views for Django

Simplify common tasks in views by utilizing modules!

# ToDo:
Cleaning up the code to work with Python 2 and Python 3.

Cleaning up documentation to make it more presentable.

Write Usage Documentation


# Your first modular view
*rough draft*

The core of a modular view

```python
class HomePage(ModularView):
  modules = [
    
  ]
```
All modules extend the `ViewModule` class. The `ViewModule`s are invoked in the order they are created

```python
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
```

Upon Entry, the view will call it's `dispatch` method. This will invoke the dispatch method on all `ViewModule`s.
Then, the view will call it's `get`, `post`, `put`, or `delete` method depending on the method used for the request.
This will invoke the same method on each view module.

View Modules are always invoked in the order they are listed.

The first module to return a `Response` will be sent to the client. This can happen on either `dispatch` or the given request methods function.

Both `ModularView` and `ViewModule` classes have a `lookup_value` method.
This will check if the given value exists in the request's GET, POST, or url parameters.
If the value to lookup is `callable` it will be called with the parameters of `request, view, *args, **kwargs` where
`*args, **kwargs` are passed through from `dispatch`

The `modules` property contains all of the modules the view will use. Let's look at some basic ones.

```python
class HomePage(ModularView):
  modules = [
    RenderTemplate('home.html'),
  ]
```

This will simply render the given template. 

The context of the template is dict stored under `view.template_context`

A less primitive approach is using Layouts

*we need to explain how the Layout system works*

```python
class HomePage(ModularView):
  modules = [
    RenderPartial('body', 'home-body.html'),
    RenderPartial('sidebar', 'home-sidebar.html'),
    RenderLayout('sidebar-layout.html', 'base.html')
  ]
```

Loading a model

```python
class BlogPost(ModularView):
  modules = [
    LoadModel(Post, 'post', {'id': 'post_id'}),
    # ... Render Modules
  ]
```
The first parameter being the model class, the second is the name used to reference the model, the third being is what's used to lookup the correct model.

The example is the equivalent of `Post.objects.get(id=post_id)` where `post_id` is aquired from the `lookup_value` function above.

All loaded models are stored on the view under `view.models[model_name]` and passed to the template context as `view.template_context[model_name]`.
