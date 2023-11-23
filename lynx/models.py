from django.db import models
from django.conf import settings

class Link(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_viewed_at = models.DateTimeField(null=True)

    original_url = models.URLField(max_length=2000)

    # Extracted metadata
    cleaned_url = models.URLField(max_length=1000)
    hostname = models.CharField(max_length=500, blank=True)
    article_date = models.DateField(null=False) # Published date of the article
    author = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=500, blank=True)
    excerpt = models.TextField(blank=True)
    header_image_url = models.URLField(blank=True)

    # Variations of the content
    article_html = models.TextField(blank=True)
    raw_text_content = models.TextField(blank=True)
    full_page_html = models.TextField(blank=True)

    # Extras
    summary = models.TextField(blank=True) # AI summary if generated
    read_time_seconds = models.IntegerField(blank=True)
    read_time_display = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']