from .models import Publisher
from django.db.models.functions import Lower


def publisher_list(request):
    """Return a list of publishers from the database for templates.

    Each item is a dict: `{'name': <display>, 'slug': <slug>}`.
    """
    qs = Publisher.objects.all().order_by(Lower('name'))
    publisher_items = [{"name": p.name, "slug": p.slug} for p in qs]
    return {"publisher_list": publisher_items}
