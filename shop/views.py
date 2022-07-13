from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseRedirect
from .models import Product, Contact, Orders, OrderUpdate
from django.contrib.auth.models import User
from django.contrib import messages
from math import ceil
from django.contrib.auth import authenticate, login, logout
import json
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
 

def index(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    dave = {'allProds': allProds}
    return render(request, 'shop/index.html', dave)



def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    thank = False
    if request.method == "POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True
        return render(request, 'shop/contact.html', {'thank': thank})
    return render(request, 'shop/contact.html', {'thank': thank})


def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        name = request.POST.get('name', '')
        password = request.POST.get('password')
        user = authenticate(username=name, password=password)
        if user is not None:
            try:
                order = Orders.objects.filter(order_id=orderId, email=email)
                if len(order) > 0:
                    update = OrderUpdate.objects.filter(order_id=orderId)
                    updates = []
                    for item in update:
                        updates.append({'text': item.update_desc, 'time': item.timestamp})
                        response = json.dumps({"status": "success", "updates": updates, "itemsJson": order[0].items_json}, default=str)
                    return HttpResponse(response)
                else:
                    return HttpResponse('{"status":"noitem"}')
            except Exception as e:
                return HttpResponse('{"status":"error"}')
        else:
            return HttpResponse('{"status":"Invalid"}')
    return render(request, 'shop/tracker.html')


def orderView(request):
    if request.user.is_authenticated:
        current_user = request.user
        orderHistory = Orders.objects.filter(userId=current_user.id)
        if len(orderHistory) == 0:
            messages.info(request, "You have not ordered.")
            return render(request, 'shop/orderView.html')
        return render(request, 'shop/orderView.html', {'orderHistory': orderHistory})
    return render(request, 'shop/orderView.html')


def searchMatch(query, item):
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower() or query in item.desc or query in item.product_name or query in item.category or query in item.desc.upper() or query in item.product_name.upper() or query in item.category.upper():
        return True
    else:
        return False


def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    dave = {'allProds': allProds, "msg": ""}
    if len(allProds) == 0 or len(query) < 3:
        dave = {'msg': "No item available. Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', dave)

        # def sendsms():
        #     account_sid = "AC153247b4e012242b51bae56b3b91c6c0"
        #     auth_token = "7973d03de9ac4d133de10bc5c19eb65d"
        #     client = Client(account_sid, auth_token)

        #     message = client.messages \
        #                     .create(
        #                         body="It is me Dave ",
        #                         from_='+19895841984',
        #                         to='phone'
        #                     )

        #     print('message send succesfully')

def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        user_id = request.POST.get('user_id', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, userId=user_id, name=name, email=email, address=address, city=city, state=state, zip_code=zip_code, phone=phone, amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The Order has been Placed")
        update.save()
        thank = True
        id = order.order_id

        account_sid = "AC153247b4e012242b51bae56b3b91c6c0"
        auth_token = "7973d03de9ac4d133de10bc5c19eb65d"
        client = Client(account_sid, auth_token)
        message = client.messages \
                    .create(
                        body=f"Welcome {name}, Dave Restaurant Your order ID is {id}, your order is {items_json}, Total Payment {amount} Birr ",
                        from_='+19895841984',
                        to=f'{phone}'
                    )
        
        if 'onlinePay' in request.POST:
            	return render(request, 'shop/simple_checkout.html', {'thank': thank, 'id': id})
        
        elif 'cashOnDelivery' in request.POST:
            return render(request, 'shop/checkout.html', {'thank': thank, 'id': id})
    return render(request, 'shop/checkout.html')


def productView(request, myid):
    product = Product.objects.filter(id=myid)
    # print(product)
    return render(request, 'shop/prodView.html', {'product': product[0]})


def handeLogin(request):
    if request.method == "POST":
        # Get the post parameters
        loginusername = request.POST['loginusername']
        loginpassword = request.POST['loginpassword']

        user = authenticate(username=loginusername, password=loginpassword)
        if user is not None:
            login(request, user)
            messages.success(request, "Successfully Logged In")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.warning(request, "Invalid credentials! Please try again")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return HttpResponse("404- Not found")


def handleSignUp(request):
    if request.method == "POST":
        # Get the post parameters
        username = request.POST['username']
        f_name = request.POST['f_name']
        l_name = request.POST['l_name']
        email = request.POST['email1']
        phone = request.POST['phone']
        password = request.POST['password']
        password1 = request.POST['password1']

        # check for errorneous input
        if (password1 != password):
            messages.warning(request, " Passwords do not match")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        try:
            user = User.objects.get(username=username)
            messages.warning(request, " Username Already taken. Try with different Username.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except User.DoesNotExist:
            # Create the user
            myuser = User.objects.create_user(username=username, email=email, password=password)
            myuser.first_name = f_name
            myuser.last_name = l_name
            myuser.phone = phone
            myuser.save()
            messages.success(request, " Your Account has been successfully created")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponse("404 - Not found")


def handleLogout(request):
    logout(request)
    messages.success(request, "Successfully logged out")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


