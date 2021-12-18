import json
from django.shortcuts import redirect, render
from django.http import JsonResponse
from .models import *
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import stripe
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import registerForm

# Create your views here.

@login_required
def store(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'store/store.html', context)

@login_required
def searched(request):
    if request.method == 'POST':  
        search_text = request.POST["search_box"]
        if(search_text == ''):
            return redirect('store')
        else:
            records= Product.objects.filter(Q(category__contains= search_text) | Q(name__contains=search_text))
            return render(request, 'store/searched.html', {"records":records})
    

def Signin(request):
    if request.user.is_authenticated:
        messages.success(request, 'Account was already created or You have not logged out')
        return redirect('login_request')
    else:
        if request.method == 'POST':
            form = registerForm(request.POST)
            if form.is_valid():
                # form.save()
                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')
                password = form.cleaned_data.get('password1')
                user = User.objects.create_user(username=username, password=password)
                customer = Customer()
                customer.user = user
                customer.name = username
                customer.email = email
                customer.save()
                return redirect('login_request')
            else:
                # messages.error(request, "Invalid username or password")
                return redirect('Signin')
        else:
            form = registerForm()
            context = {'form': form}
            return render(request, 'store/Signin.html', context)
			

def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('store')
            else:
                messages.error(request, "Invalid username or password")
                return redirect('login_request')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login_request')

    form = AuthenticationForm()
    context = {'form': form}
    return render(request, 'store/login_request.html', context)

def logout_request(request):
    if request.method =='POST':
        logout(request)
        return redirect("login_request")

@login_required
def seller(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['PDF']
        ext = os.path.splitext(uploaded_file.name)[1]
        valid_extensions = ['.pdf', '.doc', '.docx']
        if not ext in valid_extensions:
            return render(request, 'store/seller.html')
        request.user.pdfURL = uploaded_file
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
    return render(request, 'store/seller.html')


@login_required
def add_products(request):
    return render(request, 'store/add_products.html')

@login_required
def process_products(request):
    if request.method == 'POST':
        user = request.user.customer
        if(user.is_seller == True):
            uploaded_file = request.FILES['image']
            ext = os.path.splitext(uploaded_file.name)[1]
            valid_extensions = ['.png', '.jpg', '.jpeg', '.tiff']
            if not ext in valid_extensions:
                return render(request, 'store/add_products.html')
            fs = FileSystemStorage()
            product = Product()
            product.name = request.POST['name']
            product.price = request.POST['price']
            product.description = request.POST['description']
            product.category = request.POST['category']
            product.image = uploaded_file
            product.owner = user
            product.save()
            fs.save(uploaded_file.name, uploaded_file)
    return redirect("add_products")

@login_required
def cart(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    context = {'items': items, 'order': order}
    return render(request, 'store/cart.html', context)
    
@login_required
def checkout(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    context = {'items': items, 'order': order}
    return render(request, 'store/checkout.html', context)
    
@login_required
def updateItem(request):
    data = json.loads(request.body)
    productID = data['productID']
    action = data['action']

    customer = request.user.customer
    product = Product.objects.get(id=productID)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if (action == 'add'):
        orderItem.quantity = (orderItem.quantity + 1)

    elif (action == 'remove'):
        orderItem.quantity = (orderItem.quantity - 1)
    orderItem.save()
    if (action == 'delete'):
        if(customer.is_seller == True):
            if(customer.id == product.customer.id):
                product.delete()
                product.save()

    if(orderItem.quantity <= 0):
        orderItem.delete()

    return JsonResponse('Item was editted', safe=False)

@login_required
def payment(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    context = {'order': order}
    return render(request, 'store/payment.html', context)

@login_required
def create_payment(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    total = sum([item.get_total for item in items])
    stripe_charge_token = request.POST.get('stripeToken')
    desc = 'Payment of ₹' + str(total) + 'from ' + str(customer.user)
    try:
        charge = stripe.Charge.create(amount=int(total)*100,currency="inr",source=stripe_charge_token,description=desc)
        messages.success(request, "Stripe Payment Successful")
        return redirect('complete_payment', tran_id=charge['id'], amount=int(float(total)))
    except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(request, f"{err.get('message')}")
            return redirect("payment")
    except stripe.error.RateLimitError as e:
        messages.warning(request, "Rate limit error")
        return redirect("payment")
    except stripe.error.InvalidRequestError as e:
        messages.warning(request, "Invalid parameters")
        return redirect("payment")
    except stripe.error.AuthenticationError as e:
        messages.warning(request, "Not authenticated")
        return redirect("payment")
    except stripe.error.APIConnectionError as e:
        messages.warning(request, "Network error")
        return redirect("payment")
    except stripe.error.StripeError as e:
        messages.warning(
            request, "Something went wrong. You were not charged. Please try again.")
        return redirect("payment")
    except Exception as e:
        messages.warning(
            request, "A serious error occurred. We have been notified." + str(e))
        return redirect("payment")


@login_required
def complete_payment(request, tran_id, amount):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    payment = Payment()
    payment.customer = customer
    payment.amount = amount
    payment.stripe_charge_id = tran_id
    payment.save()
    order.complete = True
    order.payment = payment
    order.save()
    return redirect('store')