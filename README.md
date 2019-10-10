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
All modules extend the `ViewModule` class. The `ViewModule`s are invoked in the order they are loaded

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
``

View -> `dispatch`
  Run the

The `modules` property contains all of the modules this view will use. Let's look at some basic ones.

```python
class HomePage(ModularView):
  modules = [
    RenderTemplate('home.html'),
  ]
```

this will simply render the given template. A less primitive approach is using Layouts

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

The example is the equivalent of `Post.objects.get(id=post_id)` where post_id can come from either a GET or POST parameter, or a parameter in the url.

You can access the model as **post** in any of your templates
