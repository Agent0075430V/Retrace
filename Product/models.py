from django.db import models

# Create your models here.
class Product(models.Model):
    LIVE=1
    INACTIVE=0
    DELETE_CHOICES = [
        (LIVE, 'Live'),(INACTIVE, 'Inactive'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(choices=[('Electronics', 'Electronics'), ('Clothing', 'Clothing'), ('Stationery', 'Stationery'), ('Other', 'Other')], max_length=50)
    status = models.CharField(choices=[('Lost', 'Lost'), ('Found', 'Found')], max_length=10)
    location = models.CharField(max_length=255)
    date_reported = models.DateTimeField()
    deleted_status = models.IntegerField(choices=DELETE_CHOICES, default=LIVE)
    image = models.ImageField(upload_to='media/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        ordering = ['-created_at']  
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Image for {self.product.name}"
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['-uploaded_at']
