from django.db import models

class Link(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_viewed_at = models.DateTimeField(null=True)

    url = models.URLField(max_length=1000)
    hostname = models.CharField(max_length=200, blank=True)
    article_date = models.DateField(null=False) # Published date of the article
    author = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    excerpt = models.TextField(blank=True)

    # Parsed/generated content
    summary = models.TextField(blank=True) # AI summary if requested
    markdown_content = models.TextField(blank=True)
    raw_text_content = models.TextField(blank=True)
    header_image_url = models.URLField(blank=True)
  
    read_time_seconds = models.IntegerField(blank=True)
    read_time_display = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']