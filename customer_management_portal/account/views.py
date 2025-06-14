# ========== IMPORTS ==========
from django.shortcuts import render, redirect
from django.forms import inlineformset_factory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages

from .models import Customer, Product, Order
from .forms import OrderForm, CreateUserForm, CustomerForm
from .filters import OrderFilter
from .decorators import unauthenticated_user, allowed_users, admin_only

# ========== AUTH VIEWS ==========

@unauthenticated_user
def registerPage(request):
    # Show the registration form and handle user signup
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')

            # Automatically assign new users to "customer" group
            group, _ = Group.objects.get_or_create(name='customer')
            user.groups.add(group)

            # Create linked customer profile
            Customer.objects.create(
                user=user,
                name=user.username,
                email=user.email,
            )

            messages.success(request, f'Account created for {username}')
            return redirect('login')

    return render(request, 'accounts/register.html', {'form': form})


@unauthenticated_user
def loginPage(request):
    # Basic login logic — redirects based on user group
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # Route users to different dashboards
            group = user.groups.first().name if user.groups.exists() else None
            if group == 'admin':
                return redirect('home')
            elif group == 'customer':
                return redirect('user-page')
            else:
                messages.warning(request, "Group not recognized.")
        else:
            messages.error(request, 'Username or password is incorrect.')

    return render(request, 'accounts/login.html')


def LogoutUser(request):
    # Logs out the current user and redirects to login page
    logout(request)
    return redirect('login')


# ========== ADMIN DASHBOARD ==========

@login_required(login_url='login')
@admin_only
def home(request):
    # Admin dashboard showing key stats and recent orders
    all_orders = Order.objects.all().order_by('-date_created')
    recent_orders = all_orders[:5]  # Safe to slice here

    customers = Customer.objects.all()

    context = {
        'orders': recent_orders,
        'customers': customers,
        'total_orders': all_orders.count(),
        'total_customers': customers.count(),
        'delivered': all_orders.filter(status='Delivered').count(),
        'pending': all_orders.filter(status='Pending').count(),
    }
    return render(request, 'accounts/dashboard.html', context)


# ========== CUSTOMER PAGE ==========

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def userPage(request):
    # Customer view: shows order stats and recent activity
    try:
        customer = request.user.customer
        all_orders = customer.order_set.all().order_by('-date_created')
        recent_orders = all_orders[:5]

        context = {
            'orders': recent_orders,
            'total_orders': all_orders.count(),
            'delivered': all_orders.filter(status='Delivered').count(),
            'pending': all_orders.filter(status='Pending').count(),
            'customer_name': customer.name,
        }
        return render(request, 'accounts/user.html', context)

    except Customer.DoesNotExist:
        # If something’s off with the profile, logout
        messages.error(request, "Customer profile not found.")
        return redirect('logout')


@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def accountSettings(request):
    # Profile update view for customers
    customer = request.user.customer
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")

    return render(request, 'accounts/account_settings.html', {'form': form})


# ========== ADMIN VIEWS ==========

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def product(request):
    # Admin view: shows list of products
    products = Product.objects.all()
    return render(request, 'accounts/product.html', {'products': products})


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def customer(request, pk):
    # Admin view: shows individual customer and order history
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()

    myFilter = OrderFilter(request.GET, queryset=orders)
    filtered_orders = myFilter.qs

    context = {
        'customer': customer,
        'orders': filtered_orders,
        'order_count': filtered_orders.count(),
        'myFilters': myFilter,
    }
    return render(request, 'accounts/customer.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def createOrder(request, pk):
    # Admin can create multiple orders for a customer
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('product', 'status'), extra=7)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)

    if request.method == 'POST':
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('home')

    return render(request, 'accounts/order_form.html', {'formset': formset})


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def UpdateOrder(request, pk):
    # Admin can edit an existing order
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('home')

    return render(request, 'accounts/order_form.html', {'form': form})


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def deleteOrder(request, pk):
    # Admin can delete an order
    order = Order.objects.get(id=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('home')

    return render(request, 'accounts/delete.html', {'item': order})


# ========== CUSTOMER PLACE ORDER ==========

@login_required(login_url='login')
@allowed_users(allowed_roles=['customer'])
def placeOrder(request):
    # Customers can place an order (product is selected from form)
    customer = request.user.customer
    form = OrderForm()

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = customer  # Assign logged-in customer
            order.save()
            messages.success(request, 'Order placed successfully!')
            return redirect('user-page')

    return render(request, 'accounts/place_order.html', {'form': form})


# ========== ADMIN ADD PRODUCT ==========

@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def addProduct(request):
    # Admin can add a new product to the catalog
    from .forms import ProductForm  # Safe to import here if not globally imported
    form = ProductForm()

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('product')  # Redirect to product list page

    return render(request, 'accounts/add_product.html', {'form': form})
