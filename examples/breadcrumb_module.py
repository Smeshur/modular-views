from modules import ViewModule

class Breadcrumb(ViewModule):
    """ creates a breadcrumb entry """

    def __init__(self, name, url):
        self.name = name
        self.url = url

    def dispatch(self, request, view, *args, **kwargs):
        if not hasattr(view, 'breadcrumbs'):
            view.breadcrumbs = []

        # use callback to retrieve value
        url = self.process_callback(request, view, self.url, *args, **kwargs)
        name = self.process_callback(request, view, self.name, *args, **kwargs)

        view.breadcrumbs.append((name, url))
        view.template_context['breadcrumbs'] = view.breadcrumbs