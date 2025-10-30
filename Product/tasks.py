try:
    from celery import shared_task
except Exception:
    # If Celery is not installed, provide a no-op decorator so the
    # module can be imported and the function can still be called
    # synchronously in environments without a Celery worker.
    def shared_task(*a, **k):
        def _decorator(f):
            return f
        return _decorator


@shared_task
def run_match_for_item(item_type, item_id):
    """Background task to run matching for a lost or found item.
    item_type: 'lost' or 'found'
    """
    # Import inside task to avoid heavy imports at module import time
    from .models import LostProduct, FoundProduct, MatchResult
    from .views import generate_embedding, cosine_similarity, send_match_notification

    if item_type == 'lost':
        try:
            lost = LostProduct.objects.get(pk=item_id)
        except LostProduct.DoesNotExist:
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

    elif item_type == 'found':
        try:
            found = FoundProduct.objects.get(pk=item_id)
        except FoundProduct.DoesNotExist:
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
