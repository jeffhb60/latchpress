from django.views.generic import ListView
from publishing import Entry

class HomeView(ListView):
    model = Entry
    template_name = "core/home.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Entry.objects.public().filter(kind=Entry.Kind.POST).select_related("author")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["pages"] = Entry.objects.public().filter(kind=Entry.Kind.PAGE).order_by("title")[:12]
        return data
