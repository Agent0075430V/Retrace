## ========================== views.py ==========================
import io
import numpy as np
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse

from .models import LostProduct, FoundProduct, MatchResult, Notification, RouteMap, PendingClaim

User = get_user_model()

try:
    from PIL import Image
    import torch
    import torchvision.transforms as transforms
    import torchvision.models as torch_models
    from torchvision.models import ResNet18_Weights
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# -------------------- Lazy model loading --------------------
_resnet_model = None
_preprocess = None
_device = None

def get_model():
    """Lazy loading of the ResNet model to avoid startup delays."""
    global _resnet_model, _preprocess, _device
    
    if not TORCH_AVAILABLE:
        return None, None, None
    
    if _resnet_model is None:
        try:
            _device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Use a pre-trained ResNet18 for image embeddings
            _resnet_model = torch_models.resnet18(weights=ResNet18_Weights.DEFAULT)
            _resnet_model = torch.nn.Sequential(*list(_resnet_model.children())[:-1])  # Remove final classifier
            _resnet_model = _resnet_model.to(_device)
            _resnet_model.eval()

            # Preprocessing for ResNet
            _preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])
        except Exception as e:
            print(f"Failed to load model: {e}")
            return None, None, None
            
    return _resnet_model, _preprocess, _device

# -------------------- Helper functions ------------------------
def generate_embedding(image_field):
    """Convert uploaded image to vector embedding using ResNet18."""
    if not image_field:
        return None
    
    resnet_model, preprocess, device = get_model()
    if resnet_model is None:
        return None
    
    try:
        image = Image.open(image_field).convert("RGB")
        image_tensor = preprocess(image).unsqueeze(0).to(device)

        with torch.no_grad():
            embedding = resnet_model(image_tensor)  # shape: [1, 512, 1, 1]
        
        embedding = embedding.squeeze().cpu().numpy()  # shape: [512]
        return embedding.astype(np.float32).tobytes()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def cosine_similarity(vec1, vec2):
    """Cosine similarity between two embeddings."""
    v1 = np.frombuffer(vec1, dtype=np.float32)
    v2 = np.frombuffer(vec2, dtype=np.float32)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# -------------------- Lost Product ----------------------------
def add_lost_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        email = request.POST.get("email")
        location = request.POST.get("location")

        # Create lost product with user if authenticated
        lost_data = {
            'name': name,
            'description': description,
            'image': image,
            'email': email,
            'location': location,
        }
        if request.user.is_authenticated:
            lost_data['user'] = request.user
        
        lost = LostProduct.objects.create(**lost_data)

        # Generate embedding
        lost_embedding = generate_embedding(image)
        
        if lost_embedding is not None:
            # Compare with all found products
            found_products = FoundProduct.objects.all()
            for found in found_products:
                if found.image:
                    found_embedding = generate_embedding(found.image)
                    if found_embedding is not None:
                        similarity = cosine_similarity(lost_embedding, found_embedding)

                        match_status = "Matched" if similarity >= 0.8 else "Not Matched"
                        match = MatchResult.objects.create(
                            lost_product=lost,
                            found_product=found,
                            lost_embedding=lost_embedding,
                            found_embedding=found_embedding,
                            similarity_score=similarity,
                            match_status=match_status,
                        )

                        if match_status == "Matched":
                            send_match_notification(lost, found)

        return redirect("home")  # Redirect to home since lost_detail might not exist

    return render(request, "add_lost_product.html")


# -------------------- Found Product ---------------------------
def add_found_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        email = request.POST.get("email")
        location = request.POST.get("location")

        # Create found product with user if authenticated
        found_data = {
            'name': name,
            'description': description,
            'image': image,
            'email': email,
            'location': location,
        }
        if request.user.is_authenticated:
            found_data['user'] = request.user
        
        found = FoundProduct.objects.create(**found_data)

        # Generate embedding
        found_embedding = generate_embedding(image)

        if found_embedding is not None:
            # Compare with all lost products
            lost_products = LostProduct.objects.all()
            for lost in lost_products:
                if lost.image:
                    lost_embedding = generate_embedding(lost.image)
                    if lost_embedding is not None:
                        similarity = cosine_similarity(lost_embedding, found_embedding)

                        match_status = "Matched" if similarity >= 0.8 else "Not Matched"
                        match = MatchResult.objects.create(
                            lost_product=lost,
                            found_product=found,
                            lost_embedding=lost_embedding,
                            found_embedding=found_embedding,
                            similarity_score=similarity,
                            match_status=match_status,
                        )

                        if match_status == "Matched":
                            send_match_notification(lost, found)

        return redirect("home")  # Redirect to home since found_detail might not exist

    return render(request, "add_found_product.html")


# -------------------- Notification ----------------------------
def send_match_notification(lost, found):
    """Send email notification when a match is found."""
    subject = f"Match Found for {lost.name}!"
    message = (
        f"Good news! Your lost item '{lost.name}' might match with a found item.\n\n"
        f"Found item: {found.name}\n"
        f"Description: {found.description}\n"
        f"Location: {found.location or 'Not specified'}\n"
        f"Contact: {found.email or 'Not provided'}"
    )
    
    # Send email if we have an email and settings are configured
    if lost.email and hasattr(settings, 'DEFAULT_FROM_EMAIL'):
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [lost.email])
        except Exception as e:
            print(f"Failed to send email: {e}")

    # Create notification record
    try:
        notification_data = {
            'message': message,
            'sent_via': "Email",
            'is_sent': True,
        }
        if hasattr(lost, 'user') and lost.user:
            notification_data['user'] = lost.user
        else:
            notification_data['user_contact'] = lost.email or 'Unknown'
            
        Notification.objects.create(**notification_data)
    except Exception as e:
        print(f"Failed to create notification: {e}")


# -------------------- Route Map (Stub) -----------------------
def generate_route(request, lost_id):
    lost = get_object_or_404(LostProduct, pk=lost_id)
    
    route_data = {
        "start": {"lat": lost.latitude, "lng": lost.longitude},
        "end": {"lat": lost.latitude + 0.01, "lng": lost.longitude + 0.01},
        "steps": [
            {"instruction": "Head north 500m"},
            {"instruction": "Turn right at junction"},
            {"instruction": "Arrive at location"},
        ],
    }
    # ===================== Home View =====================
def home(request):
    # You can pass any context, e.g., route_data
    route_data = {}  # or precompute as needed
    return render(request, "Home.html", {"route_data": route_data})

# ===================== Redirect View for Legacy URLs =====================
def redirect_home(request):
    """Handle legacy .html URLs and redirect to proper Django URLs"""
    from django.shortcuts import redirect
    return redirect('home')

# ===================== Form Views =====================
def report_lost_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        location = request.POST.get("location")
        date_lost = request.POST.get("date_lost")

        # Create lost product with user if authenticated
        lost_data = {
            'name': name,
            'description': description,
            'image': image,
            'email': email,
            'phone_number': phone_number,
            'location': location,
        }
        if date_lost:
            lost_data['date_lost'] = date_lost
        if request.user.is_authenticated:
            lost_data['user'] = request.user
        
        lost = LostProduct.objects.create(**lost_data)

        # Generate embedding and check for matches
        lost_embedding = generate_embedding(image)
        matches_found = 0
        
        if lost_embedding is not None:
            # Compare with all found products
            found_products = FoundProduct.objects.all()
            for found in found_products:
                if found.image:
                    found_embedding = generate_embedding(found.image)
                    if found_embedding is not None:
                        similarity = cosine_similarity(lost_embedding, found_embedding)

                        match_status = "Matched" if similarity >= 0.8 else "Not Matched"
                        match = MatchResult.objects.create(
                            lost_product=lost,
                            found_product=found,
                            lost_embedding=lost_embedding,
                            found_embedding=found_embedding,
                            similarity_score=similarity,
                            match_status=match_status,
                        )

                        if match_status == "Matched":
                            matches_found += 1
                            send_match_notification(lost, found)

        # Return success message with match info
        context = {
            'success': True,
            'lost_item': lost,
            'matches_found': matches_found
        }
        return render(request, "Lost_product.html", context)

    return render(request, "Lost_product.html")

def report_found_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        location = request.POST.get("location")
        date_found = request.POST.get("date_found")

        # Create found product with user if authenticated
        found_data = {
            'name': name,
            'description': description,
            'image': image,
            'email': email,
            'phone_number': phone_number,
            'location': location,
        }
        if date_found:
            found_data['date_found'] = date_found
        if request.user.is_authenticated:
            found_data['user'] = request.user
        
        found = FoundProduct.objects.create(**found_data)

        # Generate embedding and check for matches
        found_embedding = generate_embedding(image)
        matches_found = 0

        if found_embedding is not None:
            # Compare with all lost products
            lost_products = LostProduct.objects.all()
            for lost in lost_products:
                if lost.image:
                    lost_embedding = generate_embedding(lost.image)
                    if lost_embedding is not None:
                        similarity = cosine_similarity(lost_embedding, found_embedding)

                        match_status = "Matched" if similarity >= 0.8 else "Not Matched"
                        match = MatchResult.objects.create(
                            lost_product=lost,
                            found_product=found,
                            lost_embedding=lost_embedding,
                            found_embedding=found_embedding,
                            similarity_score=similarity,
                            match_status=match_status,
                        )

                        if match_status == "Matched":
                            matches_found += 1
                            send_match_notification(lost, found)

        # Return success message with match info
        context = {
            'success': True,
            'found_item': found,
            'matches_found': matches_found
        }
        return render(request, "Found_product.html", context)

    return render(request, "Found_product.html")

# ==================== Search Dashboard ====================
def search_items(request):
    """
    Comprehensive search dashboard for lost and found items
    """
    context = {
        'search_performed': False,
        'lost_items': [],
        'found_items': [],
        'matches': [],
        'total_results': 0,
        'search_params': {}
    }
    
    if request.method == 'GET' and (request.GET.get('q') or request.GET.get('category') or request.GET.get('location')):
        context['search_performed'] = True
        
        # Get search parameters
        search_query = request.GET.get('q', '').strip()
        category_filter = request.GET.get('category', '')
        location_filter = request.GET.get('location', '')
        item_type = request.GET.get('type', 'all')  # all, lost, found
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Store search params for template
        context['search_params'] = {
            'q': search_query,
            'category': category_filter,
            'location': location_filter,
            'type': item_type,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        # Base querysets - show all lost items by default
        lost_items = LostProduct.objects.all()
        found_items = FoundProduct.objects.all()
        
        # Apply item type filter first
        if item_type == 'lost':
            found_items = FoundProduct.objects.none()
        elif item_type == 'found':
            lost_items = LostProduct.objects.none()
        elif item_type == 'active-lost':
            # Only show items that are still lost (not found or claimed)
            lost_items = lost_items.filter(status='lost')
            found_items = FoundProduct.objects.none()
        
        # Apply text search filter
        if search_query:
            lost_items = lost_items.filter(
                name__icontains=search_query
            ) | lost_items.filter(
                description__icontains=search_query
            )
            found_items = found_items.filter(
                name__icontains=search_query
            ) | found_items.filter(
                description__icontains=search_query
            )
        
        # Apply location filter
        if location_filter:
            lost_items = lost_items.filter(location__icontains=location_filter)
            found_items = found_items.filter(location__icontains=location_filter)
        
        # Apply date filters
        if date_from:
            lost_items = lost_items.filter(date_lost__gte=date_from)
            found_items = found_items.filter(date_found__gte=date_from)
        
        if date_to:
            lost_items = lost_items.filter(date_lost__lte=date_to)
            found_items = found_items.filter(date_found__lte=date_to)
        
        # Order by most recent
        lost_items = lost_items.order_by('-created_at')
        found_items = found_items.order_by('-created_at')
        
        # Get matches for the search results
        matches = MatchResult.objects.filter(
            match_status="Matched"
        ).select_related('lost_product', 'found_product').order_by('-timestamp')
        
        if search_query:
            matches = matches.filter(
                lost_product__name__icontains=search_query
            ) | matches.filter(
                found_product__name__icontains=search_query
            )
        
        context.update({
            'lost_items': lost_items,
            'found_items': found_items,
            'matches': matches,
            'total_results': lost_items.count() + found_items.count(),
        })
    
    # Get all unique locations for filter dropdown
    all_locations = set()
    for item in LostProduct.objects.all():
        if item.location:
            all_locations.add(item.location)
    for item in FoundProduct.objects.all():
        if item.location:
            all_locations.add(item.location)
    
    context['all_locations'] = sorted(list(all_locations))
    
    # Get some stats for the dashboard
    context['stats'] = {
        'total_lost': LostProduct.objects.count(),
        'total_found': FoundProduct.objects.count(),
        'total_matches': MatchResult.objects.filter(match_status="Matched").count(),
        'recent_matches': MatchResult.objects.filter(match_status="Matched").order_by('-timestamp')[:5]
    }
    
    return render(request, "Search_dashboard.html", context)


# ==================== Mark as Found Functionality ====================
@login_required
@csrf_protect
def mark_item_as_found(request, lost_item_id):
    """
    Mark a lost item as found, create a corresponding found item, and send notifications
    (requires authentication)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        # Get the lost item
        lost_item = get_object_or_404(LostProduct, id=lost_item_id)
        
        # Check if item is already marked as found
        if lost_item.status == 'found':
            return JsonResponse({'success': False, 'error': 'Item is already marked as found'})
        
        # Get the user who found the item (if logged in)
        finder_user = request.user if request.user.is_authenticated else None
        
        # Get additional information from the request
        finder_location = request.POST.get('finder_location', '')
        finder_contact = request.POST.get('finder_contact', '')
        additional_notes = request.POST.get('additional_notes', '')
        
        # Create a new FoundProduct based on the lost item
        found_item = FoundProduct.objects.create(
            user=finder_user,
            name=lost_item.name,
            description=f"{lost_item.description}\n\nFound by: {finder_contact or 'Anonymous'}\nLocation when found: {finder_location}\nAdditional notes: {additional_notes}",
            image=lost_item.image,
            email=finder_contact,
            phone_number=lost_item.phone_number,
            location=finder_location or lost_item.location,
            latitude=lost_item.latitude,
            longitude=lost_item.longitude,
            date_found=None,  # Will be set automatically via auto_now_add
        )
        
        # Update the lost item status
        lost_item.status = 'found'
        lost_item.found_by = finder_user
        lost_item.date_found = found_item.created_at
        lost_item.save()
        
        # Send notification to the original owner
        send_item_found_notification(lost_item, found_item, finder_contact)
        
        return JsonResponse({
            'success': True, 
            'message': f'Item "{lost_item.name}" has been marked as found and the owner will be notified.',
            'found_item_id': found_item.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def send_item_found_notification(lost_item, found_item, finder_contact):
    """Send email notification to the owner when their item is marked as found"""
    if not lost_item.email:
        return
    
    subject = f"Great News! Your Lost Item '{lost_item.name}' Has Been Found!"
    
    message = f"""
Dear {lost_item.email},

Excellent news! Someone has found your lost item "{lost_item.name}" and reported it on Retrace.

Item Details:
- Name: {lost_item.name}
- Description: {lost_item.description}
- Originally lost on: {lost_item.date_lost or 'Date not specified'}
- Originally lost at: {lost_item.location_lost or lost_item.location or 'Location not specified'}

Found Item Details:
- Found at: {found_item.location or 'Location not specified'}
- Found on: {found_item.created_at.strftime('%B %d, %Y at %I:%M %p')}
- Finder contact: {finder_contact or 'Contact info not provided'}

Next Steps:
1. Contact the finder using the provided contact information to arrange pickup
2. Verify the item matches your lost item description
3. Arrange a safe meeting location for item retrieval

Thank you for using Retrace!

Best regards,
The Retrace Team
    """
    
    try:
        if hasattr(settings, 'DEFAULT_FROM_EMAIL'):
            send_mail(
                subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [lost_item.email],
                fail_silently=False
            )
            
            # Create notification record
            notification_data = {
                'message': f"Your lost item '{lost_item.name}' has been found! Check your email for details.",
                'sent_via': "Email",
                'is_sent': True,
            }
            
            if lost_item.user:
                notification_data['user'] = lost_item.user
            else:
                notification_data['user_contact'] = lost_item.email
                
            Notification.objects.create(**notification_data)
            
    except Exception as e:
        print(f"Failed to send found item notification: {e}")
        # Create notification record even if email fails
        try:
            notification_data = {
                'message': f"Your lost item '{lost_item.name}' has been found, but email notification failed.",
                'sent_via': "Email",
                'is_sent': False,
            }
            
            if lost_item.user:
                notification_data['user'] = lost_item.user
            else:
                notification_data['user_contact'] = lost_item.email
                
            Notification.objects.create(**notification_data)
        except Exception as notification_error:
            print(f"Failed to create notification record: {notification_error}")


@login_required
def get_mark_found_form(request, lost_item_id):
    """Return a form for marking an item as found (requires authentication)"""
    try:
        lost_item = get_object_or_404(LostProduct, id=lost_item_id)
        
        if lost_item.status == 'found':
            return JsonResponse({'success': False, 'error': 'Item is already marked as found'})
        
        form_html = f"""
        <div class="mark-found-form">
            <h3>Mark "{lost_item.name}" as Found</h3>
            <form id="mark-found-form-{lost_item_id}">
                <div class="form-group">
                    <label for="finder_contact">Your Contact Information:</label>
                    <input type="email" id="finder_contact" name="finder_contact" 
                           placeholder="your.email@example.com" required>
                </div>
                <div class="form-group">
                    <label for="finder_location">Where did you find it?</label>
                    <input type="text" id="finder_location" name="finder_location" 
                           placeholder="Location where item was found">
                </div>
                <div class="form-group">
                    <label for="additional_notes">Additional Notes (optional):</label>
                    <textarea id="additional_notes" name="additional_notes" 
                              placeholder="Any additional information about the condition or circumstances..."></textarea>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-success">Mark as Found & Notify Owner</button>
                    <button type="button" class="btn btn-secondary" onclick="closeMarkFoundForm()">Cancel</button>
                </div>
            </form>
        </div>
        """
        
        return JsonResponse({'success': True, 'form_html': form_html})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== All Items Listing Views ====================
def all_lost_items(request):
    """
    Display all lost items with detailed information and filtering options
    """
    # Get filtering parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    location_filter = request.GET.get('location', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Base queryset
    lost_items = LostProduct.objects.all()
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        lost_items = lost_items.filter(status=status_filter)
    
    # Apply search filter
    if search_query:
        lost_items = lost_items.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(location__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Apply location filter
    if location_filter:
        lost_items = lost_items.filter(
            models.Q(location__icontains=location_filter) |
            models.Q(location_lost__icontains=location_filter)
        )
    
    # Apply date filters
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            lost_items = lost_items.filter(date_lost__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            lost_items = lost_items.filter(date_lost__lte=date_to_obj)
        except ValueError:
            pass
    
    # Apply sorting
    valid_sort_fields = [
        'created_at', '-created_at', 'name', '-name', 
        'date_lost', '-date_lost', 'status', '-status'
    ]
    if sort_by in valid_sort_fields:
        lost_items = lost_items.order_by(sort_by)
    else:
        lost_items = lost_items.order_by('-created_at')
    
    # Get pagination
    from django.core.paginator import Paginator
    paginator = Paginator(lost_items, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique locations for filter dropdown
    all_locations = set()
    for item in LostProduct.objects.all():
        if item.location:
            all_locations.add(item.location)
        if item.location_lost:
            all_locations.add(item.location_lost)
    
    # Get statistics
    stats = {
        'total_lost': LostProduct.objects.count(),
        'active_lost': LostProduct.objects.filter(status='lost').count(),
        'found_lost': LostProduct.objects.filter(status='found').count(),
        'claimed_lost': LostProduct.objects.filter(status='claimed').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'lost_items': page_obj.object_list,
        'search_params': {
            'status': status_filter,
            'search': search_query,
            'date_from': date_from,
            'date_to': date_to,
            'location': location_filter,
            'sort': sort_by,
        },
        'all_locations': sorted(list(all_locations)),
        'stats': stats,
        'total_results': paginator.count,
    }
    
    return render(request, "all_lost_items.html", context)


def all_found_items(request):
    """
    Display all found items with detailed information and filtering options
    """
    # Get filtering parameters
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    location_filter = request.GET.get('location', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Base queryset
    found_items = FoundProduct.objects.all()
    
    # Apply search filter
    if search_query:
        found_items = found_items.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(location__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Apply location filter
    if location_filter:
        found_items = found_items.filter(
            models.Q(location__icontains=location_filter) |
            models.Q(location_found__icontains=location_filter)
        )
    
    # Apply date filters
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            found_items = found_items.filter(date_found__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            found_items = found_items.filter(date_found__lte=date_to_obj)
        except ValueError:
            pass
    
    # Apply sorting
    valid_sort_fields = [
        'created_at', '-created_at', 'name', '-name', 
        'date_found', '-date_found'
    ]
    if sort_by in valid_sort_fields:
        found_items = found_items.order_by(sort_by)
    else:
        found_items = found_items.order_by('-created_at')
    
    # Get pagination
    from django.core.paginator import Paginator
    paginator = Paginator(found_items, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique locations for filter dropdown
    all_locations = set()
    for item in FoundProduct.objects.all():
        if item.location:
            all_locations.add(item.location)
        if item.location_found:
            all_locations.add(item.location_found)
    
    # Get statistics
    stats = {
        'total_found': FoundProduct.objects.count(),
        'this_week': FoundProduct.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
        'this_month': FoundProduct.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'found_items': page_obj.object_list,
        'search_params': {
            'search': search_query,
            'date_from': date_from,
            'date_to': date_to,
            'location': location_filter,
            'sort': sort_by,
        },
        'all_locations': sorted(list(all_locations)),
        'stats': stats,
        'total_results': paginator.count,
    }
    
    return render(request, "all_found_items.html", context)

def all_claimed_items(request):
    """
    Display all claimed items with detailed information
    """
    # Get filtering parameters
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    location_filter = request.GET.get('location', '')
    sort_by = request.GET.get('sort', '-updated_at')
    
    # Base queryset - only claimed items
    claimed_items = LostProduct.objects.filter(status='claimed')
    
    # Apply search filter
    if search_query:
        claimed_items = claimed_items.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(location__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Apply location filter
    if location_filter:
        claimed_items = claimed_items.filter(
            models.Q(location__icontains=location_filter) |
            models.Q(location_lost__icontains=location_filter)
        )
    
    # Apply date filters (using date_lost for when originally lost)
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            claimed_items = claimed_items.filter(date_lost__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            claimed_items = claimed_items.filter(date_lost__lte=date_to_obj)
        except ValueError:
            pass
    
    # Apply sorting
    valid_sort_fields = [
        'created_at', '-created_at', 'updated_at', '-updated_at',
        'name', '-name', 'date_lost', '-date_lost', 'date_found', '-date_found'
    ]
    if sort_by in valid_sort_fields:
        claimed_items = claimed_items.order_by(sort_by)
    else:
        claimed_items = claimed_items.order_by('-updated_at')
    
    # Get pagination
    from django.core.paginator import Paginator
    paginator = Paginator(claimed_items, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique locations for filter dropdown
    all_locations = set()
    for item in LostProduct.objects.filter(status='claimed'):
        if item.location:
            all_locations.add(item.location)
        if item.location_lost:
            all_locations.add(item.location_lost)
    
    # Get statistics
    stats = {
        'total_claimed': LostProduct.objects.filter(status='claimed').count(),
        'claimed_today': LostProduct.objects.filter(
            status='claimed',
            updated_at__date=timezone.now().date()
        ).count(),
        'claimed_this_week': LostProduct.objects.filter(
            status='claimed',
            updated_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
        'claimed_this_month': LostProduct.objects.filter(
            status='claimed',
            updated_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'claimed_items': page_obj.object_list,
        'search_params': {
            'search': search_query,
            'date_from': date_from,
            'date_to': date_to,
            'location': location_filter,
            'sort': sort_by,
        },
        'all_locations': sorted(list(all_locations)),
        'stats': stats,
        'total_results': paginator.count,
    }
    
    return render(request, "all_claimed_items.html", context)

# ==================== Claim Item Views ====================
@login_required
@csrf_protect
def claim_item(request, lost_item_id):
    """
    Handle claiming a lost item by the owner (requires authentication)
    """
    if request.method == 'POST':
        try:
            lost_item = get_object_or_404(LostProduct, id=lost_item_id)
            
            # Check if the item is already claimed
            if lost_item.status == 'claimed':
                return JsonResponse({
                    'success': False, 
                    'error': 'This item has already been claimed.'
                })
            
            # Check if the item is found
            if lost_item.status != 'found':
                return JsonResponse({
                    'success': False, 
                    'error': 'This item must be found before it can be claimed.'
                })
            
            # Additional security: Check if user is trying to claim their own item
            claimer_email = request.POST.get('claimer_email', '').strip().lower()
            
            # Enhanced verification: Check multiple factors
            verification_passed = False
            verification_method = ""
            
            # Method 1: Email verification (if item has owner email)
            if lost_item.email and lost_item.email.lower() == claimer_email:
                verification_passed = True
                verification_method = "email"
            
            # Method 2: User account verification (if item belongs to logged-in user)
            elif lost_item.user and lost_item.user == request.user:
                verification_passed = True
                verification_method = "account"
            
            # Method 3: Admin override (if user is staff)
            elif request.user.is_staff:
                verification_passed = True
                verification_method = "admin_override"
            
            if not verification_passed:
                # Create a pending claim that requires manual verification
                pending_claim = PendingClaim.objects.create(
                    lost_item=lost_item,
                    claimer=request.user,
                    claimer_email=claimer_email,
                    claimer_name=request.POST.get('claimer_name', '').strip(),
                    claimer_phone=request.POST.get('claimer_phone', '').strip(),
                    verification_details=request.POST.get('verification_details', '').strip(),
                    created_at=timezone.now()
                )
                
                # Send verification email to original owner
                if lost_item.email:
                    try:
                        verification_link = request.build_absolute_uri(
                            reverse('verify_claim', kwargs={'claim_id': pending_claim.id})
                        )
                        send_mail(
                            subject=f'Claim Verification Required: {lost_item.name}',
                            message=f'''
Hello,

Someone has requested to claim your lost item "{lost_item.name}".

Claimer Details:
- Name: {pending_claim.claimer_name}
- Email: {pending_claim.claimer_email}
- Phone: {pending_claim.claimer_phone}
- Verification Details: {pending_claim.verification_details}

To verify this claim, please click the link below:
{verification_link}

If this is not you or you did not authorize this claim, please contact us immediately.

Best regards,
Retrace Team
                            ''',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[lost_item.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(f"Email sending failed: {e}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Claim submitted for verification. The owner will be notified to verify your identity.',
                    'pending': True
                })
            
            # Get form data
            claimer_name = request.POST.get('claimer_name', '').strip()
            claimer_phone = request.POST.get('claimer_phone', '').strip()
            verification_details = request.POST.get('verification_details', '').strip()
            
            # Basic validation
            if not claimer_name or not claimer_email:
                return JsonResponse({
                    'success': False, 
                    'error': 'Name and email are required.'
                })
            
            # Update the item status to claimed
            lost_item.status = 'claimed'
            lost_item.claimed_by = request.user
            lost_item.claimed_at = timezone.now()
            lost_item.save()
            
            # Create a notification record
            Notification.objects.create(
                user=lost_item.user,
                message=f'Your lost item "{lost_item.name}" has been claimed by {claimer_name} ({claimer_email}) via {verification_method} verification.',
                sent_via='Email',
                is_sent=True
            )
            
            # If there's a found_by user, notify them too
            if lost_item.found_by:
                Notification.objects.create(
                    user=lost_item.found_by,
                    message=f'The lost item "{lost_item.name}" that you helped find has been claimed by the owner.',
                    sent_via='Email',
                    is_sent=True
                )
                
                # Send email to the finder
                try:
                    if lost_item.found_by.email:
                        send_mail(
                            subject=f'Item Claimed: {lost_item.name}',
                            message=f'''
Hello {lost_item.found_by.username},

Great news! The lost item "{lost_item.name}" that you helped find has been successfully claimed by the owner.

Thank you for your help in reuniting this item with its owner!

Best regards,
Retrace Team
                            ''',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[lost_item.found_by.email],
                            fail_silently=False,
                        )
                except Exception as e:
                    print(f"Email sending to finder failed: {e}")
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully claimed "{lost_item.name}". Verification method: {verification_method}.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_claim_form(request, lost_item_id):
    """
    Get the claim form HTML for a specific lost item (requires authentication)
    """
    try:
        lost_item = get_object_or_404(LostProduct, id=lost_item_id)
        
        # Check if the item can be claimed
        if lost_item.status == 'claimed':
            return JsonResponse({
                'success': False,
                'error': 'This item has already been claimed.'
            })
        
        if lost_item.status != 'found':
            return JsonResponse({
                'success': False,
                'error': 'This item must be found before it can be claimed.'
            })
        
        # Generate form HTML
        form_html = f'''
        <h3>🎉 Claim Your Item: {lost_item.name}</h3>
        <p>Please provide the following information to claim this item:</p>
        
        <form id="claim-form-{lost_item_id}" method="post">
            <div style="margin-bottom: 15px;">
                <label for="claimer_name" style="display: block; font-weight: bold; margin-bottom: 5px;">
                    Your Name *
                </label>
                <input type="text" id="claimer_name" name="claimer_name" required
                       style="width: 100%; padding: 10px; border: 2px solid #e1e8ed; border-radius: 8px;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label for="claimer_email" style="display: block; font-weight: bold; margin-bottom: 5px;">
                    Your Email *
                </label>
                <input type="email" id="claimer_email" name="claimer_email" required
                       placeholder="Enter the email you used when reporting this item"
                       style="width: 100%; padding: 10px; border: 2px solid #e1e8ed; border-radius: 8px;">
            </div>
            
            <div style="margin-bottom: 15px;">
                <label for="claimer_phone" style="display: block; font-weight: bold; margin-bottom: 5px;">
                    Your Phone Number
                </label>
                <input type="tel" id="claimer_phone" name="claimer_phone"
                       style="width: 100%; padding: 10px; border: 2px solid #e1e8ed; border-radius: 8px;">
            </div>
            
            <div style="margin-bottom: 20px;">
                <label for="verification_details" style="display: block; font-weight: bold; margin-bottom: 5px;">
                    Additional Verification Details
                </label>
                <textarea id="verification_details" name="verification_details" rows="3"
                          placeholder="Provide any additional details to verify ownership (e.g., purchase date, unique identifiers, etc.)"
                          style="width: 100%; padding: 10px; border: 2px solid #e1e8ed; border-radius: 8px; resize: vertical;"></textarea>
            </div>
            
            <div style="text-align: center;">
                <button type="submit" style="background: #27ae60; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 16px;">
                    🎉 Claim This Item
                </button>
            </div>
        </form>
        
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px; font-size: 14px; color: #666;">
            <strong>Note:</strong> By claiming this item, you confirm that you are the rightful owner. 
            False claims may result in account suspension.
        </div>
        '''
        
        return JsonResponse({
            'success': True,
            'form_html': form_html
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })

def verify_claim(request, claim_id):
    """
    Verify a pending claim using the verification token
    """
    try:
        token = request.GET.get('token')
        pending_claim = get_object_or_404(PendingClaim, id=claim_id, verification_token=token)
        
        # Check if claim is expired
        if pending_claim.is_expired():
            pending_claim.status = 'expired'
            pending_claim.save()
            messages.error(request, 'This verification link has expired.')
            return redirect('all_lost_items')
        
        # Check if already processed
        if pending_claim.status != 'pending':
            messages.info(request, 'This claim has already been processed.')
            return redirect('all_lost_items')
        
        lost_item = pending_claim.lost_item
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'approve':
                # Approve the claim
                pending_claim.status = 'approved'
                pending_claim.verified_at = timezone.now()
                pending_claim.save()
                
                # Update the lost item
                lost_item.status = 'claimed'
                lost_item.claimed_by = pending_claim.claimer
                lost_item.claimed_at = timezone.now()
                lost_item.save()
                
                # Send confirmation email to claimer
                try:
                    send_mail(
                        subject=f'Claim Approved: {lost_item.name}',
                        message=f'''
Hello {pending_claim.claimer_name},

Your claim for "{lost_item.name}" has been approved by the owner.

You can now contact them to arrange pickup/return.

Best regards,
Retrace Team
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[pending_claim.claimer_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Email sending failed: {e}")
                
                messages.success(request, 'Claim approved successfully!')
                
            elif action == 'reject':
                # Reject the claim
                pending_claim.status = 'rejected'
                pending_claim.verified_at = timezone.now()
                pending_claim.save()
                
                # Send rejection email to claimer
                try:
                    send_mail(
                        subject=f'Claim Rejected: {lost_item.name}',
                        message=f'''
Hello {pending_claim.claimer_name},

Your claim for "{lost_item.name}" has been rejected by the owner.

If you believe this is an error, please contact support.

Best regards,
Retrace Team
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[pending_claim.claimer_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Email sending failed: {e}")
                
                messages.warning(request, 'Claim rejected.')
            
            return redirect('all_lost_items')
        
        # Show verification form
        context = {
            'pending_claim': pending_claim,
            'lost_item': lost_item,
        }
        return render(request, 'verify_claim.html', context)
        
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('all_lost_items')
