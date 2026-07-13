import os
import requests
from django.utils.dateparse import parse_date

RAWG_KEY = os.getenv("RAWG_API_KEY")


def fetch_rawg(slug):
    """
    Fetch RAWG API data for a given slug.
    Example slug: 'elden-ring'
    """
    url = f"https://api.rawg.io/api/games/{slug}?key={RAWG_KEY}"
    response = requests.get(url)

    # If RAWG fails, return empty dict to avoid crashes
    if response.status_code != 200:
        return {}

    return response.json()


def sync_post_from_rawg(post):
    if not post.rawg_slug:
        return

    data = fetch_rawg(post.rawg_slug)
    if not data:
        return

    post.rawg_id = data.get("id")
    post.title = data.get("name", post.title)
    post.description = data.get("description_raw", post.description)

    released = data.get("released")
    post.release_date = parse_date(released) if released else post.release_date

    post.rating = data.get("rating", post.rating)

    platforms = data.get("platforms", [])
    post.platforms = [
        p["platform"]["name"] for p in platforms if "platform" in p
    ]

    genres = data.get("genres", [])
    post.genre = [g["name"] for g in genres]

    tags = data.get("tags", [])
    post.tags = [t["name"] for t in tags]

    developers = data.get("developers", [])
    if developers:
        post.developer = developers[0]["name"]

    publishers = data.get("publishers", [])

    # ⭐ NEW: Save publishers into your ManyToMany field
    from publishers.models import Publisher
    post.publishers.clear()
    for pub in publishers:
        publisher_obj, created = Publisher.objects.get_or_create(name=pub["name"])
        post.publishers.add(publisher_obj)

    post.save()
