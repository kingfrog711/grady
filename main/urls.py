from django.urls import path
from main.views import show_main, publish_product, publish_product_ajax, show_product, show_xml, show_json, show_xml_by_id, show_json_by_id, register, login_user, logout_user, edit_product, delete_product, login_flutter, register_flutter, logout_flutter, proxy_image

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('publish_product/', publish_product, name='publish_product'),
    path('publish_product_ajax/', publish_product_ajax, name='publish_product_ajax'),
    path('product/<str:id>/', show_product, name='show_product'),
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path("xml/<uuid:shop_id>/", show_xml_by_id, name="show_xml_by_id"),
    path("json/<uuid:shop_id>/", show_json_by_id, name="show_json_by_id"),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('news/<uuid:id>/edit', edit_product, name='edit_product'),
    path('news/<uuid:id>/delete', delete_product, name='delete_product'),
        # Flutter authentication endpoints
        path('auth/login/', login_flutter, name='login_flutter'),
        path('auth/register/', register_flutter, name='register_flutter'),
        path('auth/logout/', logout_flutter, name='logout_flutter'),
        # Image proxy endpoint for CORS
        path('proxy/image/', proxy_image, name='proxy_image'),
    ]