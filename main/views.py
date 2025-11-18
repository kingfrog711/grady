from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.core import serializers
from main.forms import ShopForm
from main.models import Shop

#assignment 3
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import datetime
import json
from django.urls import reverse
from django.utils import timezone
import urllib.request
import urllib.parse
import ssl


@login_required(login_url='/login')
def show_main(request):
    # Check if this is an AJAX/JSON request
    if request.headers.get('Accept') == 'application/json' or 'application/json' in request.headers.get('Accept', ''):
        filter_type = request.GET.get("filter", "all")
        sort_type = request.GET.get("sort")

        if filter_type == "all":
            shop_list = Shop.objects.all()
        else:
            shop_list = Shop.objects.filter(user=request.user)

        if sort_type == "ascending":
            shop_list = shop_list.order_by("price")
        else:
            shop_list = shop_list.order_by("-price")

        data = [
            {
                'id': str(shop.id),
                'name': shop.name,
                'price': shop.price,
                'description': shop.description,
                'thumbnail': shop.thumbnail if shop.thumbnail else None,  # Explicitly handle None
                'category': shop.category,
                'is_featured': shop.is_featured,
                'size': shop.size,
                'stock': shop.stock,
                'released': shop.released.isoformat() if shop.released else None,
                'user_id': shop.user_id,
                'user_username': shop.user.username if shop.user_id else None,
            }
            for shop in shop_list
        ]
        # Debug: Print thumbnail values
        print("Products in JSON response (show_main):")
        for item in data:
            print(f"  - {item['name']}: thumbnail={item['thumbnail']} (type: {type(item['thumbnail'])})")
        
        response = JsonResponse(data, safe=False)
        # Add CORS headers for Flutter web
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    # Regular HTML request
    filter_type = request.GET.get("filter", "all")  # default 'all'
    sort_type = request.GET.get("sort")

    if filter_type == "all":
        shop_list = Shop.objects.all()
    else:
        shop_list = Shop.objects.filter(user=request.user)

    if sort_type == "ascending":
        shop_list = shop_list.order_by("price")
    else:
        shop_list = shop_list.order_by("-price")

        
    context = {
        'npm' : '2406453461',
        'name': 'Gunata Prajna Putra Sakri',
        'class': 'PBP KKI',
        'shop': shop_list,
        'last_login': request.COOKIES.get('last_login', 'Never'),
    }

    return render(request, "main.html", context)

@login_required(login_url='/login')
def publish_product(request):
    form = ShopForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        shop_entry = form.save(commit = False)
        shop_entry.user = request.user
        shop_entry.released = timezone.now()
        shop_entry.save()
        return redirect('main:show_main')

    context = {'form': form}
    return render(request, "publish_product.html", context)

@csrf_exempt
def publish_product_ajax(request):
    # Handle OPTIONS for CORS preflight (for Flutter web)
    if request.method == 'OPTIONS':
        response = JsonResponse({}, status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization, Accept'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    # Check authentication manually (for Flutter requests)
    if not request.user.is_authenticated:
        response = JsonResponse({
            'status': 'error',
            'error': {'__all__': ['Authentication required. Please log in first.']}
        }, status=401)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    if request.method == 'POST':
        try:
            print(f"Publish product request method: {request.method}")
            print(f"Content-Type: {request.content_type}")
            print(f"Body: {request.body}")
            
            # Handle both JSON and form data
            if request.content_type == 'application/json' or 'application/json' in (request.content_type or ''):
                data = json.loads(request.body)
                # JSON data might have string values that need conversion
                # Convert numeric strings to ints
                for key in ['price', 'size', 'stock']:
                    if key in data:
                        if isinstance(data[key], str):
                            try:
                                data[key] = int(round(float(data[key])))
                            except (ValueError, TypeError):
                                data[key] = 0
                        elif isinstance(data[key], (int, float)):
                            data[key] = int(round(float(data[key])))
                # Convert boolean string
                if 'is_featured' in data and isinstance(data['is_featured'], str):
                    data['is_featured'] = data['is_featured'].lower() in ['true', '1', 'yes']
            else:
                # Form data - extract first value from lists (form data can have multiple values)
                data = {}
                for key, value in request.POST.items():
                    if isinstance(value, list):
                        data[key] = value[0] if len(value) > 0 else ''
                    else:
                        data[key] = value
                
                # Convert form data types (handle list values from form)
                for key in ['price', 'size', 'stock']:
                    if key in data:
                        val = data[key]
                        # Convert to int, handling both string and numeric types
                        if isinstance(val, str):
                            try:
                                # Handle decimal numbers by rounding
                                data[key] = int(round(float(val)))
                            except (ValueError, TypeError):
                                data[key] = 0
                        elif isinstance(val, (int, float)):
                            data[key] = int(round(float(val)))
                        else:
                            data[key] = 0
                
                # Handle boolean
                if 'is_featured' in data:
                    is_featured_val = data['is_featured']
                    data['is_featured'] = is_featured_val in [True, 'true', 'on', 1, '1', 'True', 'True']
            
            print(f"Parsed data: {data}")
            
            # Convert empty strings to None for optional fields (URLField doesn't accept empty strings)
            if 'thumbnail' in data:
                if data['thumbnail'] == '' or data['thumbnail'] is None:
                    data['thumbnail'] = None
                elif isinstance(data['thumbnail'], list):
                    # Handle list case
                    thumbnail_val = data['thumbnail'][0] if len(data['thumbnail']) > 0 else ''
                    data['thumbnail'] = None if thumbnail_val == '' else thumbnail_val
            
            # Ensure category is a string, not a list
            if 'category' in data and isinstance(data['category'], list):
                data['category'] = data['category'][0] if len(data['category']) > 0 else 'jersey'
            
            # Convert checkbox/boolean value
            if 'is_featured' in data:
                is_featured_val = data['is_featured']
                if isinstance(is_featured_val, list):
                    is_featured_val = is_featured_val[0]
                data['is_featured'] = is_featured_val in [True, 'true', 'on', 1, '1', 'True']
            
            # Ensure required fields have defaults and correct types
            if 'price' in data:
                if isinstance(data['price'], str):
                    try:
                        data['price'] = int(round(float(data['price'])))
                    except (ValueError, TypeError):
                        data['price'] = 0
                elif isinstance(data['price'], float):
                    data['price'] = int(round(data['price']))
                elif not isinstance(data['price'], int):
                    data['price'] = 0
            else:
                data['price'] = 0
                
            if 'size' not in data or data['size'] is None:
                data['size'] = 0
            elif isinstance(data['size'], str):
                try:
                    data['size'] = int(round(float(data['size'])))
                except (ValueError, TypeError):
                    data['size'] = 0
            elif isinstance(data['size'], float):
                data['size'] = int(round(data['size']))
                
            if 'stock' not in data or data['stock'] is None:
                data['stock'] = 0
            elif isinstance(data['stock'], str):
                try:
                    data['stock'] = int(round(float(data['stock'])))
                except (ValueError, TypeError):
                    data['stock'] = 0
            elif isinstance(data['stock'], float):
                data['stock'] = int(round(data['stock']))
            
            form = ShopForm(data)
            
            if form.is_valid():
                shop_entry = form.save(commit=False)
                shop_entry.user = request.user
                shop_entry.released = timezone.now()
                shop_entry.save()
                
                print(f"Product saved successfully: {shop_entry.id}")
                
                response = JsonResponse({
                    'status': 'success',
                    'message': 'Product published successfully!',
                    'id': str(shop_entry.id)
                }, status=201)
                # Add CORS headers
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Credentials'] = 'true'
                return response
            else:
                # Format form errors for better display
                error_messages = {}
                for field, errors in form.errors.items():
                    error_messages[field] = [str(error) for error in errors]
                
                print(f"Form validation errors: {error_messages}")
                
                response = JsonResponse({
                    'status': 'error',
                    'error': error_messages
                }, status=400)
                response['Access-Control-Allow-Origin'] = '*'
                return response
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            response = JsonResponse({
                'status': 'error',
                'error': {'__all__': ['Invalid JSON data']}
            }, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as e:
            print(f"Exception in publish_product_ajax: {e}")
            import traceback
            traceback.print_exc()
            response = JsonResponse({
                'status': 'error',
                'error': {'__all__': [str(e)]}
            }, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    
    response = JsonResponse({
        'status': 'error',
        'error': {'__all__': ['Invalid request method']}
    }, status=405)
    response['Access-Control-Allow-Origin'] = '*'
    return response

@login_required(login_url='/login')
def show_product(request, id):
    shop = get_object_or_404(Shop, pk=id)

    context = {
        'product': shop
    }

    return render(request, "product_detail.html", context)

def show_xml(request):
    shop_list = Shop.objects.all()
    xml_data = serializers.serialize("xml", shop_list)
    return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    shop_list = Shop.objects.all()
    data = [
        {
            'id': str(shop.id),
            'name': shop.name,
            'price': shop.price,
            'description': shop.description,
            'thumbnail': shop.thumbnail if shop.thumbnail else None,  # Explicitly handle None
            'category': shop.category,
            'is_featured': shop.is_featured,
            'size': shop.size,
            'stock': shop.stock,
            'released': shop.released.isoformat() if shop.released else None,
            'user_id': shop.user_id,
            'user_username': shop.user.username if shop.user_id else None,
        }
        for shop in shop_list
    ]
    # Debug: Print thumbnail values
    print("Products in JSON response:")
    for item in data:
        print(f"  - {item['name']}: thumbnail={item['thumbnail']} (type: {type(item['thumbnail'])})")
    
    response = JsonResponse(data, safe=False)
    # Add CORS headers for Flutter web
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Credentials'] = 'true'
    return response

def show_xml_by_id(request, shop_id):
    try:
        product = Shop.objects.filter(pk=shop_id)
        xml_data = serializers.serialize("xml", product)
        return HttpResponse(xml_data, content_type="application/xml")
    except Shop.DoesNotExist:
        return HttpResponse(status=404)

def show_json_by_id(request, product_id):
    try:
        product = Shop.objects.select_related('user').get(pk=product_id)
        
        data = {
            'id': str(product.id),
            'name': product.name,
            'price': product.price,
            'description': product.description,
            'thumbnail': product.thumbnail,
            'category': product.category,
            'is_featured': product.is_featured,
            'size': product.size,
            'stock': product.stock,
            'released': product.released.isoformat() if product.released else None,
            'user_id': product.user_id,
            'user_username': product.user.username if product.user_id else None,
        }
        return JsonResponse(data)
        
    except Shop.DoesNotExist:
        return JsonResponse({'detail': 'Product not found'}, status=404)

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('main:login')
    context = {'form':form}
    return render(request, 'register.html', context)

def login_user(request):
   if request.method == 'POST':
      form = AuthenticationForm(data=request.POST)

      if form.is_valid():
        user = form.get_user()
        login(request, user)
        response = HttpResponseRedirect(reverse("main:show_main"))
        response.set_cookie('last_login', str(timezone.now()))
        return response

   else:
      form = AuthenticationForm(request)
   context = {'form': form}
   return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

def edit_product(request, id):
    product = get_object_or_404(Shop, pk=id)
    form = ShopForm(request.POST or None, instance=product)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "edit_product.html", context)


def delete_product(request, id):
    product = get_object_or_404(Shop, pk=id)
    product.delete()
    return HttpResponseRedirect(reverse('main:show_main'))


# Flutter authentication endpoints
@csrf_exempt
def login_flutter(request):
    # Handle OPTIONS for CORS preflight (for Flutter web)
    if request.method == 'OPTIONS':
        response = JsonResponse({}, status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse({
            "status": False,
            "message": f"Method {request.method} not allowed. Use POST."
        }, status=405)
    
    print(f"Login request method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"POST data: {dict(request.POST)}")
    print(f"Body: {request.body}")
    
    # Handle both JSON and form data
    username = None
    password = None
    
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            print(f"JSON data - username: {username}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data"
            }, status=400)
    else:
        # Handle form data (application/x-www-form-urlencoded)
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Form data - username: {username}")
    
    if not username or not password:
        print("Missing username or password")
        return JsonResponse({
            "status": False,
            "message": "Username and password are required"
        }, status=400)
    
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            print(f"Login successful for user: {user.username}")
            response = JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Login successful!"
            }, status=200)
            # CORS headers are handled by middleware, but ensure they're set here too
            # Use headers attribute for Django 3.2+
            if hasattr(response, 'headers'):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Credentials'] = 'true'
            else:
                response['Access-Control-Allow-Origin'] = '*'
                response['Access-Control-Allow-Credentials'] = 'true'
            return response
        else:
            print("User account is disabled")
            response = JsonResponse({
                "status": False,
                "message": "Login failed, account is disabled."
            }, status=401)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    else:
        print("Authentication failed - invalid credentials")
        response = JsonResponse({
            "status": False,
            "message": "Login failed, please check your username or password."
        }, status=401)
        response['Access-Control-Allow-Origin'] = '*'
        return response

@csrf_exempt
def register_flutter(request):
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password1 = data.get('password1')
                password2 = data.get('password2')
            except json.JSONDecodeError:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid JSON data"
                }, status=400)
        else:
            username = request.POST.get('username')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
        
        if not username or not password1 or not password2:
            return JsonResponse({
                "status": False,
                "message": "Username, password1, and password2 are required"
            }, status=400)
        
        if password1 != password2:
            return JsonResponse({
                "status": False,
                "message": "Passwords do not match."
            }, status=400)
        
        if len(password1) < 8:
            return JsonResponse({
                "status": False,
                "message": "Password must be at least 8 characters."
            }, status=400)
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.create_user(username=username, password=password1)
            response = JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Account created successfully!"
            }, status=201)
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response
        except Exception as e:
            response = JsonResponse({
                "status": False,
                "message": f"Registration failed: {str(e)}"
            }, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    
    return JsonResponse({
        "status": False,
        "message": "Invalid request method."
    }, status=405)

@csrf_exempt
def logout_flutter(request):
    username = request.user.username if request.user.is_authenticated else None
    logout(request)
    response = JsonResponse({
        "username": username,
        "status": True,
        "message": "Logout successful!"
    }, status=200)
    # Add CORS headers for Flutter web
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Credentials'] = 'true'
    return response

@csrf_exempt
def proxy_image(request):
    """
    Proxy endpoint to fetch images and serve them with CORS headers.
    This solves CORS issues when Flutter web tries to load external images.
    """
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = '*'
        return response
    
    image_url = request.GET.get('url')
    
    print(f"Proxy image request: url={image_url}")
    
    if not image_url:
        print("Missing url parameter")
        response = HttpResponse('Missing url parameter', status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    try:
        # Decode URL if it's encoded
        image_url = urllib.parse.unquote(image_url)
        print(f"Decoded URL: {image_url}")
        
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Fetch the image
        req = urllib.request.Request(image_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        req.add_header('Accept', 'image/webp,image/apng,image/*,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.9')
        
        print(f"Fetching image from: {image_url}")
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            image_data = response.read()
            # Get content type from response, default to image/jpeg
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            # Ensure it's a valid image content type
            if not content_type.startswith('image/'):
                content_type = 'image/jpeg'
            
            print(f"Image fetched successfully, size: {len(image_data)} bytes, content-type: {content_type}")
            
            # Create response with CORS headers
            http_response = HttpResponse(image_data, content_type=content_type)
            http_response['Access-Control-Allow-Origin'] = '*'
            http_response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            http_response['Access-Control-Allow-Headers'] = '*'
            http_response['Cache-Control'] = 'public, max-age=86400'  # Cache for 1 day
            
            return http_response
    except urllib.error.HTTPError as e:
        print(f"HTTP Error fetching image: {e.code} - {e.reason}")
        print(f"URL: {image_url}")
        response = HttpResponse(f'HTTP Error: {e.code} - {e.reason}', status=e.code)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except urllib.error.URLError as e:
        print(f"URL Error fetching image: {e}")
        print(f"URL: {image_url}")
        response = HttpResponse(f'Error fetching image: {str(e)}', status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        response = HttpResponse(f'Unexpected error: {str(e)}', status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response


