from django.db import models

# Create your models here.
class Location(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']  
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

class LocationLog(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Log for {self.location.name} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']  
        verbose_name = 'Location Log'
        verbose_name_plural = 'Location Logs'

class LocationSettings(models.Model):
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='settings')
    notifications_enabled = models.BooleanField(default=True)
    alert_threshold = models.IntegerField(default=5)  # Example threshold
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.location.name}"
    
    class Meta:
        ordering = ['-created_at']  
        verbose_name = 'Location Setting'
        verbose_name_plural = 'Location Settings'

class LocationReport(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='reports')
    reporter_name = models.CharField(max_length=100)
    reporter_contact = models.CharField(max_length=100)
    report_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report for {self.location.name} by {self.reporter_name}"
    
    class Meta:
        ordering = ['-report_date']  
        verbose_name = 'Location Report'
        verbose_name_plural = 'Location Reports'


