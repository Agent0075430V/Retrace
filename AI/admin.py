from django.contrib import admin
from .models import AImodels, LostProduct, FoundProduct, MatchResult, Notification, RouteMap, PendingClaim

# Register your models here.
admin.site.register(AImodels)
admin.site.register(LostProduct)
admin.site.register(FoundProduct)
admin.site.register(MatchResult)
admin.site.register(Notification)
admin.site.register(RouteMap)

@admin.register(PendingClaim)
class PendingClaimAdmin(admin.ModelAdmin):
    list_display = ['id', 'lost_item', 'claimer_name', 'claimer_email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['claimer_name', 'claimer_email', 'lost_item__name']
    readonly_fields = ['verification_token', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lost_item', 'claimer')
