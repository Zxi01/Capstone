from django.shortcuts import render, get_object_or_404
from django.views import generic
from .models import Post
import json
import os
from django.conf import settings
from django.utils.text import slugify

# Create your views here.


class PostList(generic.ListView):
    queryset = Post.objects.all()
    template_name = "reviews/index.html"
    paginate_by = 6

    def get_queryset(self):
        """Optionally filter posts by a `genre` GET parameter (slug).

        The genre mapping is loaded from `reviews/fixtures/games.json` (the
        same source used elsewhere). If `?genre=<slug>` is provided, this
        returns posts whose fixture `genre` includes that slug.
        """
        qs = Post.objects.filter(status=1)
        genre_slug = self.request.GET.get('genre')
        if not genre_slug:
            return qs.order_by('-created_on')

        fixtures_path = os.path.join(
            settings.BASE_DIR, 'reviews', 'fixtures', 'games.json'
        )
        matching_slugs = set()
        try:
            with open(fixtures_path, 'r', encoding='utf-8') as fh:
                games = json.load(fh)
        except Exception:
            games = []

        for g in games:
            fields = g.get('fields', {})
            g_list = fields.get('genre') or []
            if isinstance(g_list, (list, tuple)):
                for item in g_list:
                    if slugify(str(item)) == genre_slug:
                        matching_slugs.add(fields.get('slug'))
            else:
                if slugify(str(g_list)) == genre_slug:
                    matching_slugs.add(fields.get('slug'))

        if matching_slugs:
            return (
                qs.filter(slug__in=list(matching_slugs))
                .order_by('-created_on')
            )

        return qs.none()


def post_detail(request, slug):
    """
    Display an individual :model:`reviews.Post`.

    **Context**

    ``post``
        An instance of :model:`reviews.Post`.

    **Template:**

    :template:`reviews/post_detail.html`
    """

    queryset = Post.objects.filter(status=1)
    post = get_object_or_404(queryset, slug=slug)

    return render(
        request,
        "reviews/post_detail.html",
        {"post": post},
    )
