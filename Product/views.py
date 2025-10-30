from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProductImage, Product
from AI.models import Notification, RouteMap, MatchResult, FoundProduct, LostProduct

# Create your views here.
def report_lost(request):
    if request.method == 'GET':
        return render(request, 'Lost_product.html')
    
    if request.method == 'POST':
        # Get form data with correct field names from template
        name = request.POST.get("name")
        description = request.POST.get("description")
        category = request.POST.get("category")
        status = "Lost"  # Default status
        image = request.FILES.get("image")
        location = request.POST.get("location")
        date_reported = request.POST.get("date_lost")  # Template uses 'date_lost'
        reporter_contact = request.POST.get("phone_number")  # Template uses 'phone_number'
        email = request.POST.get("email")
        
        # Set default values for missing fields
        reporter_name = email.split('@')[0] if email else "Anonymous"
        additional_info = ""
        
        # Validate required fields
        if not all([name, description, location, date_reported, email]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'Lost_product.html')
        
        try:
            # Create and save the lost product
            lost_product = LostProduct(
                name=name,
                description=description,
                status=status,
                category=category or "General",
                image=image,
                location=location,
                date_reported=date_reported,
                reporter_name=reporter_name,
                reporter_contact=reporter_contact or "",
                email=email,
                additional_info=additional_info,
                user=request.user if request.user.is_authenticated else None
            )
            lost_product.save()
            messages.success(request, "Lost product reported successfully!")
            return render(request, 'Lost_product.html')
        except Exception as e:
            messages.error(request, f"Error saving report: {str(e)}")
            return render(request, 'Lost_product.html')

def report_found(request):
    if request.method == 'GET':
        return render(request, 'Found_product.html')
    
    if request.method == 'POST':
        # Get form data with correct field names from template
        name = request.POST.get("name")
        description = request.POST.get("description")
        category = request.POST.get("category")
        status = "Found"  # Default status
        image = request.FILES.get("image")
        location = request.POST.get("location")
        date_reported = request.POST.get("date_found")  # Template uses 'date_found'
        reporter_contact = request.POST.get("phone_number")  # Template uses 'phone_number'
        email = request.POST.get("email")
        
        # Set default values for missing fields
        reporter_name = email.split('@')[0] if email else "Anonymous"
        additional_info = ""
        
        # Validate required fields
        if not all([name, description, location, date_reported, email]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'Found_product.html')
        
        try:
            # Create and save the found product
            found_product = FoundProduct(
                name=name,
                description=description,
                status=status,
                category=category or "General",
                image=image,
                location=location,
                date_reported=date_reported,
                reporter_name=reporter_name,
                reporter_contact=reporter_contact or "",
                email=email,
                additional_info=additional_info,
                user=request.user if request.user.is_authenticated else None
            )
            found_product.save()
            messages.success(request, "Found product reported successfully!")
            return render(request, 'Found_product.html')
        except Exception as e:
            messages.error(request, f"Error saving report: {str(e)}")
            return render(request, 'Found_product.html')

def Product(request):
    return render(request, 'Dashboard.html', {'style': 'Style.css'})

