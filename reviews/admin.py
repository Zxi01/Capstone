from django.contrib import admin
from .models import Post, Comment
from django_summernote.admin import SummernoteModelAdmin
from .rawg import sync_post_from_rawg


@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):

    list_display = ('title', 'slug', 'status', 'created_on')
    search_fields = ['title', 'content']
    list_filter = ('status', 'created_on')
    prepopulated_fields = {'slug': ('title',)}
    summernote_fields = ('content',)

    def save_model(self, request, obj, form, change):
        """
        When a Post is saved in admin:
        - Save normally
        - If rawg_slug is set, sync RAWG data into the model
        """
        super().save_model(request, obj, form, change)

        if obj.rawg_slug:
            sync_post_from_rawg(obj)


# Register your models here.
admin.site.register(Comment)
