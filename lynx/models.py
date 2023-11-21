from django.db import models

class Link(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    url = models.URLField(max_length=1000)
    hostname = models.CharField(max_length=200, blank=True)
    article_date = models.DateField(null=True) # Published date of the article
    author = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    excerpt = models.TextField(blank=True)

    # Parsed/generated content
    summary = models.TextField(blank=True) # AI summary if requested
    markdown_content = models.TextField(blank=True)
    json_parse_result = models.JSONField(null=True, blank=False)
    header_image_url = models.URLField(blank=True, default="")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']