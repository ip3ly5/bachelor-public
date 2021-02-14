from django.contrib import admin

from .models import Post, Comment, Category, Quote, PostImage, Postcode, CancelledFrozenTo


# Register your models here.
class PostImageAdmin(admin.StackedInline):
    model = PostImage

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageAdmin]

    class Meta:
       model = Post

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(Postcode)
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(Quote)
admin.site.register(CancelledFrozenTo)
