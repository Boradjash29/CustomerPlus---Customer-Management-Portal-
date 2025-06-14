from django.urls import path
from . import views


urlpatterns = [
    path('register/',views.registerPage,name="register"),
    path('login/',views.loginPage,name="login"),
    path('logout/',views.LogoutUser,name="logout"),
    path('',views.home,name="home"),
    path('user/',views.userPage,name="user-page"),
    path('account/',views.accountSettings,name="account"),
    path('product/',views.product,name="product"),
    path('add-product/', views.addProduct, name='add-product'),
    path('place_order/', views.placeOrder, name='place_order'),
    path('customer/<str:pk>/',views.customer,name="customer"),
    path('create_order/<str:pk>/',views.createOrder,name="create_order"),
    path('Update_order/<str:pk>/',views.UpdateOrder,name="Update_order"),
    path('Delete_order/<str:pk>/',views.deleteOrder,name="Delete_order")

]