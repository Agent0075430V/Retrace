from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class AImodels(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    route_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name
class LostProduct(models.Model):
    STATUS_CHOICES = [
        ('lost', 'Lost'),
        ('found', 'Found'),
        ('claimed', 'Claimed'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    date_lost = models.DateField(null=True, blank=True)
    location_lost = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    contact_info = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='lost_product_images/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='lost')
    found_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='found_items')
    date_found = models.DateTimeField(null=True, blank=True)
    claimed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_items')
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name        
class FoundProduct(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    date_found = models.DateField(null=True, blank=True)
    location_found = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    contact_info = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='found_product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
class MatchResult(models.Model):
    id = models.AutoField(primary_key=True)
    lost_product = models.ForeignKey(LostProduct, on_delete=models.CASCADE)
    found_product = models.ForeignKey(FoundProduct, on_delete=models.CASCADE)
    lost_embedding = models.BinaryField(blank=True, null=True)
    found_embedding = models.BinaryField(blank=True, null=True)
    similarity_score = models.FloatField()
    threshold_used = models.FloatField(default=0.8)
    match_status = models.CharField(max_length=50, default="Not Matched")
    notified_users = models.BooleanField(default=False)
    match_score = models.FloatField(null=True, blank=True)  # Keep for backward compatibility
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Match {self.id}: {self.lost_product.name} - {self.found_product.name}"
class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_contact = models.CharField(max_length=255, null=True, blank=True)  # Keep for backward compatibility
    message = models.TextField()
    sent_via = models.CharField(max_length=50, default="Email")
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.id} to {self.user_contact or self.user}"
class RouteMap(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(LostProduct, on_delete=models.CASCADE, null=True, blank=True)  # For serializer compatibility
    lost_product = models.ForeignKey(LostProduct, on_delete=models.CASCADE, related_name='route_maps', null=True, blank=True)
    found_product = models.ForeignKey(FoundProduct, on_delete=models.CASCADE, null=True, blank=True)
    route_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.lost_product and self.found_product:
            return f"RouteMap {self.id} for {self.lost_product.name} to {self.found_product.name}"
        elif self.product:
            return f"RouteMap {self.id} for {self.product.name}"
        return f"RouteMap {self.id}"

class PendingClaim(models.Model):
    """Model to handle pending claim verifications"""
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    id = models.AutoField(primary_key=True)
    lost_item = models.ForeignKey(LostProduct, on_delete=models.CASCADE, related_name='pending_claims')
    claimer = models.ForeignKey(User, on_delete=models.CASCADE)
    claimer_name = models.CharField(max_length=100)
    claimer_email = models.EmailField()
    claimer_phone = models.CharField(max_length=20, blank=True, null=True)
    verification_details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Pending claim for {self.lost_item.name} by {self.claimer_name}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.verification_token:
            import secrets
            self.verification_token = secrets.token_urlsafe(32)
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=7)  # 7 days to verify
        super().save(*args, **kwargs)
