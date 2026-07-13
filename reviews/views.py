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
from .utils import fetch_rawg_data

# Create your views here.


class PostList(generic.ListView):
    queryset = Post.objects.all()
    template_name = "reviews/index.html"
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context["object_list"]

        for post in posts:
            post.extra = fetch_rawg_data(post.slug)

        # ⭐ NEW: dynamic genres from RAWG + DB
        from itertools import chain
        context["genres"] = set(chain.from_iterable(
            Post.objects.values_list("genre", flat=True)
        ))

        # ⭐ NEW: dynamic publishers from RAWG + DB
        from publishers.models import Publisher
        context["publishers"] = Publisher.objects.all()

        return context

    
    def get_queryset(self):
        qs = Post.objects.filter(status=1)
        genre_slug = self.request.GET.get('genre')
        publisher_slug = self.request.GET.get('publisher')

        # ⭐ RAWG genre filtering
        if genre_slug:
            base_qs = qs.filter(
                genre__icontains=genre_slug.replace('-', ' ')
            )
        else:
            base_qs = qs

        # ⭐ RAWG publisher filtering
        if publisher_slug:
            from publishers.models import Publisher

            pub = Publisher.objects.filter(slug=publisher_slug).first()
            if pub:
                base_qs = base_qs.filter(publishers=pub)
            else:
                # fallback: match developer text
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
    extra = fetch_rawg_data(post.slug)
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
            "extra": extra,
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
            messages.add_message(
                request, messages.ERROR,
                'Error updating comment!')

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
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own comments!')

    return HttpResponseRedirect(reverse('post_detail', args=[slug]))
