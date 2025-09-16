import uuid
from django.db import models

class Shop(models.Model):
    CATEGORY_CHOICES = [
        ('jersey', 'Jersey'),
        ('shoes', 'Football Shoes'),
        ('ball', 'Football'),
        ('accessories', 'Accessories'),
        ('equipment', 'Training Equipment'),
        ('fan_merch', 'Fan Merchandise'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    price = models.PositiveIntegerField(default=0)
    description = models.TextField()
    thumbnail = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='update')
    is_featured = models.BooleanField(default=False)
    size =models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    released = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name
