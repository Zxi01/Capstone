from django.shortcuts import render, get_object_or_404, reverse
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Post, Comment
import json
import os
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from .forms import CommentForm

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
        publisher_slug = self.request.GET.get('publisher')

        # No filters -> return all published posts
        if not genre_slug and not publisher_slug:
            return qs.order_by('-created_on')

        # Load fixtures only if genre filtering requested
        matching_slugs = set()
        if genre_slug:
            fixtures_path = os.path.join(
                settings.BASE_DIR, 'reviews', 'fixtures', 'games.json'
            )
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

        # Start with genre-filtered set (if requested) otherwise all published
        if genre_slug:
            if matching_slugs:
                base_qs = qs.filter(slug__in=list(matching_slugs))
            else:
                base_qs = qs.none()
        else:
            base_qs = qs

        # Apply publisher filtering if requested. Try DB relation first,
        # then fall back to matching post.developer text if needed.
        if publisher_slug:
            try:
                from publishers.models import Publisher
            except Exception:
                Publisher = None

            if Publisher:
                pub = Publisher.objects.filter(slug=publisher_slug).first()
                if pub:
                    # match posts linked to publisher OR where developer text equals publisher name
                    base_qs = base_qs.filter(Q(publishers=pub) | Q(developer__iexact=pub.name))
                else:
                    # fallback: try matching developer text from slug (replace hyphens)
                    name_guess = publisher_slug.replace('-', ' ')
                    base_qs = base_qs.filter(developer__iexact=name_guess)
            else:
                name_guess = publisher_slug.replace('-', ' ')
                base_qs = base_qs.filter(developer__iexact=name_guess)

        return base_qs.order_by('-created_on')


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
    comments = post.comments.all().order_by("-created_on")
    comment_count = post.comments.filter(approved=True).count()

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted and awaiting approval'
            )

    comment_form = CommentForm()

    return render(
        request,
        "reviews/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
        },
    )


def comment_edit(request, slug, comment_id):
    """
    view to edit comments
    """
    if request.method == "POST":

        queryset = Post.objects.filter(status=1)
        post = get_object_or_404(queryset, slug=slug)
        comment = get_object_or_404(Comment, pk=comment_id)
        comment_form = CommentForm(data=request.POST, instance=comment)

        if comment_form.is_valid() and comment.author == request.user:
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.approved = False
            comment.save()
            messages.add_message(request, messages.SUCCESS, 'Comment Updated!')
        else:
            messages.add_message(request, messages.ERROR, 'Error updating comment!')

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))


def comment_delete(request, slug, comment_id):
    """
    view to delete comment
    """
    queryset = Post.objects.filter(status=1)
    post = get_object_or_404(queryset, slug=slug)
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
    else:
        messages.add_message(request, messages.ERROR, 'You can only delete your own comments!')

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))
