from django.shortcuts import render, get_object_or_404, reverse
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Post, Comment
import json
import os
from django.conf import settings
from django.utils.text import slugify
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