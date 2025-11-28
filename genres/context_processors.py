from .models import Genre
from django.db.models.functions import Lower


def genre_list(request):
    """Return a list of genres from the database for templates.

    Each item is a dict: `{'name': <display>, 'slug': <slug>}`.
    """
    qs = Genre.objects.all().order_by(Lower('name'))
    genre_items = [{"name": g.name, "slug": g.slug} for g in qs]
    return {"genre_list": genre_items}
