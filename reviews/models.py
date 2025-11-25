from django.db import models
from django.contrib.auth.models import User

STATUS = (
    (0, "Draft"),
    (1, "Published"),
)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default="")
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    content = models.TextField(blank=True, default="")
    excerpt = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=STATUS, default=0)

    # Add these extra fields to match your fixture
    developer = models.CharField(max_length=100, blank=True)
    release_date = models.DateField(null=True, blank=True)
    platforms = models.JSONField(default=list, blank=True)
    genre = models.JSONField(default=list, blank=True)
    rating = models.FloatField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.title} | written by {self.author}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="commenter")
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_on"]

    def __str__(self):
        return f"Comment {self.body} by {self.author}"
