from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

# Import from AI app models instead of Product app models
from AI.models import LostProduct, FoundProduct, MatchResult, Notification, RouteMap
from AI.serializers import (
    LostProductSerializer, FoundProductSerializer, MatchResultSerializer, NotificationSerializer, RouteMapSerializer
)

# Avoid heavy imports at module import time
try:
    import torch
    import clip
    from PIL import Image
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False


class LostProductViewSet(viewsets.ModelViewSet):
    queryset = LostProduct.objects.all()
    serializer_class = LostProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        lost = serializer.save(user=self.request.user)
        from django.conf import settings
        if getattr(settings, 'CELERY_ENABLED', False):
            try:
                from .tasks import run_match_for_item
                run_match_for_item.delay('lost', lost.id)
            except Exception:
                # Fall back to inline matching on failure to enqueue
                pass
            return

        # Inline matching fallback
        if not AI_AVAILABLE:
            return

        try:
            from AI.views import generate_embedding, cosine_similarity, send_match_notification
        except Exception:
            return

        if not lost.image:
            return

        lost_embedding = generate_embedding(lost.image)
        for found in FoundProduct.objects.all():
            if not found.image:
                continue
            found_embedding = generate_embedding(found.image)
            similarity = cosine_similarity(lost_embedding, found_embedding)
            status_str = "Matched" if similarity >= 0.8 else "Not Matched"
            MatchResult.objects.create(
                lost_product=lost,
                found_product=found,
                lost_embedding=lost_embedding if lost_embedding else b'',
                found_embedding=found_embedding if found_embedding else b'',
                similarity_score=similarity,
                match_status=status_str,
            )
            if status_str == "Matched":
                send_match_notification(lost, found)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def match(self, request, pk=None):
        lost = self.get_object()
        if not AI_AVAILABLE:
            return Response({"detail": "AI dependencies (torch/clip) are not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Lazy import helper functions
        from AI.views import generate_embedding, cosine_similarity, send_match_notification

        lost_embedding = generate_embedding(lost.image) if lost.image else None
        results = []
        for found in FoundProduct.objects.all():
            if not found.image or not lost_embedding:
                continue
            found_embedding = generate_embedding(found.image)
            similarity = cosine_similarity(lost_embedding, found_embedding)
            status_str = "Matched" if similarity >= 0.8 else "Not Matched"
            MatchResult.objects.create(
                lost_product=lost,
                found_product=found,
                lost_embedding=lost_embedding if lost_embedding else b'',
                found_embedding=found_embedding if found_embedding else b'',
                similarity_score=similarity,
                match_status=status_str,
            )
            if status_str == "Matched":
                send_match_notification(lost, found)
            results.append({'found_id': found.id, 'similarity': similarity, 'status': status_str})

        return Response({'matches': results})


class FoundProductViewSet(viewsets.ModelViewSet):
    queryset = FoundProduct.objects.all()
    serializer_class = FoundProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        found = serializer.save(user=self.request.user)
        from django.conf import settings
        if getattr(settings, 'CELERY_ENABLED', False):
            try:
                from .tasks import run_match_for_item
                run_match_for_item.delay('found', found.id)
            except Exception:
                pass
            return

        if not AI_AVAILABLE:
            return

        try:
            from AI.views import generate_embedding, cosine_similarity, send_match_notification
        except Exception:
            return

        if not found.image:
            return

        found_embedding = generate_embedding(found.image)
        for lost in LostProduct.objects.all():
            if not lost.image:
                continue
            lost_embedding = generate_embedding(lost.image)
            similarity = cosine_similarity(lost_embedding, found_embedding)
            status_str = "Matched" if similarity >= 0.8 else "Not Matched"
            MatchResult.objects.create(
                lost_product=lost,
                found_product=found,
                lost_embedding=lost_embedding if lost_embedding else b'',
                found_embedding=found_embedding if found_embedding else b'',
                similarity_score=similarity,
                match_status=status_str,
            )
            if status_str == "Matched":
                send_match_notification(lost, found)


class MatchResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MatchResult.objects.all()
    serializer_class = MatchResultSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class RouteMapViewSet(viewsets.ModelViewSet):
    queryset = RouteMap.objects.all()
    serializer_class = RouteMapSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
