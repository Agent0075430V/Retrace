from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.conf import settings

from .models import LostProduct, FoundProduct, MatchResult, Notification, RouteMap
from .serializers import (
    LostProductSerializer, FoundProductSerializer, MatchResultSerializer, NotificationSerializer, RouteMapSerializer
)
from .utils import generate_embedding, cosine_similarity, send_match_notification  # moved AI helpers to utils

# AI availability check
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

        if getattr(settings, 'CELERY_ENABLED', False):
            try:
                from .tasks import run_match_for_item
                run_match_for_item.delay('lost', lost.id)
            except Exception:
                pass
            return

        if not AI_AVAILABLE or not lost.image:
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
                lost_embedding=lost_embedding or b'',
                found_embedding=found_embedding or b'',
                similarity_score=similarity,
                match_status=status_str,
            )
            if status_str == "Matched":
                send_match_notification(lost, found)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def match(self, _request, _pk=None):
        lost = self.get_object()

        if not AI_AVAILABLE:
            return Response({"detail": "AI dependencies not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
                lost_embedding=lost_embedding or b'',
                found_embedding=found_embedding or b'',
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

        if getattr(settings, 'CELERY_ENABLED', False):
            try:
                from .tasks import run_match_for_item
                run_match_for_item.delay('found', found.id)
            except Exception:
                pass
            return

        if not AI_AVAILABLE or not found.image:
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
                lost_embedding=lost_embedding or b'',
                found_embedding=found_embedding or b'',
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


# DRF router setup
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'lost-products', LostProductViewSet, basename='lostproduct')
router.register(r'found-products', FoundProductViewSet, basename='foundproduct')
router.register(r'match-results', MatchResultViewSet, basename='matchresult')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'route-maps', RouteMapViewSet, basename='routemap')

# Make sure ProfileViewSet/UserProfileViewSet are imported properly from another file
# router.register(r'profiles', ProfileViewSet)
# router.register(r'userprofiles', UserProfileViewSet)

urlpatterns = router.urls
