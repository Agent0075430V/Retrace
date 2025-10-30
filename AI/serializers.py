from rest_framework import serializers
from .models import LostProduct, FoundProduct, MatchResult, Notification, RouteMap


class LostProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostProduct
        fields = ['id', 'user', 'name', 'description', 'image', 'email', 'phone_number', 'location', 'latitude', 'longitude', 'date_lost', 'location_lost', 'contact_info', 'created_at']
        read_only_fields = ['user', 'created_at']


class FoundProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundProduct
        fields = ['id', 'user', 'name', 'description', 'image', 'email', 'phone_number', 'location', 'latitude', 'longitude', 'date_found', 'location_found', 'contact_info', 'created_at']
        read_only_fields = ['user', 'created_at']


class MatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchResult
        fields = ['id', 'lost_product', 'found_product', 'similarity_score', 'threshold_used', 'match_status', 'notified_users', 'timestamp', 'created_at']
        read_only_fields = ['created_at', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'sent_via', 'is_sent', 'created_at', 'sent_at']
        read_only_fields = ['created_at', 'sent_at']


class RouteMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteMap
        fields = ['id', 'product', 'lost_product', 'found_product', 'route_data', 'created_at']
        read_only_fields = ['created_at']
