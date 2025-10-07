from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core import serializers
from main.forms import ShopForm
from main.models import Shop

#assignment 3
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone


@login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        shop_list = Shop.objects.all()
    else:
        shop_list = Shop.objects.filter(user=request.user)

    context = {
        'npm' : '2406453461',
        'name': 'Gunata Prajna Putra Sakri',
        'class': 'PBP KKI',
        'shop': shop_list,
        'last_login': request.COOKIES.get('last_login', 'Never'),
    }

    return render(request, "main.html", context)

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
            'thumbnail': shop.thumbnail,
            'category': shop.category,
            'is_featured': shop.is_featured,
            'size': shop.size,
            'stock': shop.stock,
            'released': shop.released.isoformat() if shop.released else None,
        }
        for shop in shop_list
    ]
    return JsonResponse(data, safe=False)

def show_xml_by_id(request, shop_id):
    try:
        product = Shop.objects.filter(pk=shop_id)
        xml_data = serializers.serialize("xml", product)
        return HttpResponse(xml_data, content_type="application/xml")
    except Shop.DoesNotExist:
        return HttpResponse(status=404)

from django.http import JsonResponse
from .models import Shop # <-- Must import the Product model
from datetime import datetime # Required for date handling (though not strictly necessary here since isoformat is used)

def show_json_by_id(request, product_id):
    try:
        product = Product.objects.select_related('user').get(pk=product_id)
        
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
        
    except Product.DoesNotExist:
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
        response.set_cookie('last_login', str(datetime.datetime.now()))
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


