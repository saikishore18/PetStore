from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from .models import Product, Order, Orderhistory, Contactenquiry, Cart
from django.db.models import Q
from django.core.mail import send_mail
import random
import razorpay


# Create your views here.
def user_login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        n = request.POST['uname']
        p = request.POST['upass']
        # print(n)
        # print(p)
        u = authenticate(username=n, password=p)
        # print(u)
        if u is not None:
            login(request, u)
            return redirect('/product')
        else:
            context = {}
            context['errmsg'] = 'Invalid UserName and Password'
            return render(request, 'login.html', context)


def user_logout(request):
    logout(request)
    return redirect('/login')


def product(request):
    p = Product.objects.filter(is_active=True)
    context = {}
    context['data'] = p
    return render(request, 'index.html', context)


def productdetail(request, pid):
    p = Product.objects.filter(id=pid)
    context = {}
    context['data'] = p
    return render(request, 'product_detail.html', context)


def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        context = {}
        n = request.POST['uname']
        p = request.POST['upass']
        cp = request.POST['ucpass']
        if n == '' or p == '' or cp == '':
            context['errmsg'] = 'Field can not be NULL'
            return render(request, 'register.html', context)
        elif len(p) < 8:
            context['errmsg'] = 'Password must be 8 Characters'
            return render(request, 'register.html', context)
        elif p != cp:
            context['errmsg'] = 'Password and Confirm password must be same'
            return render(request, 'register.html', context)
        else:
            try:
                u = User.objects.create(username=n, email=n)
                u.set_password(p)
                u.save()
                context['success'] = 'User Created Successfully'
                return render(request, 'register.html', context)
            except Exception:
                context['errmsg'] = 'User Already Exists, Please Login..!'
                return render(request, 'register.html', context)


def landing(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        se = Contactenquiry(name=name, email=email, message=message)
        se.save()
    return render(request, 'index.html')


def addtocart(request, pid):
    if request.user.is_authenticated:
        context = {}
        u = User.objects.filter(id=request.user.id)
        p = Product.objects.filter(id=pid)
        # Check Product is Exist or not
        q1 = Q(uid=u[0])
        q2 = Q(pid=p[0])
        c = Cart.objects.filter(q1 & q2)
        n = len(c)
        context['data'] = p
        if n == 1:
            context['errmsg'] = 'Pet Already Exist'
            return render(request, 'product_detail.html', context)
        else:
            c = Cart.objects.create(uid=u[0], pid=p[0])
            c.save()
            context['msg'] = 'Pet added Successfully in the cart'
            return render(request, 'product_detail.html', context)
    else:
        return redirect('/login')


def viewcart(request):
    c = Cart.objects.filter(uid=request.user.id)
    context = {}
    context['data'] = c
    sum = 0
    for x in c:
        sum = sum + x.pid.price * x.qty
    context['total'] = sum
    context['n'] = len(c)
    return render(request, 'cart.html', context)


def remove(request, cid):
    c = Cart.objects.filter(id=cid)
    c.delete()
    return redirect('/viewcart')


def orderhistory(request):
    return render(request, 'orderhistory.html')


def placeorder(request):
    c = Cart.objects.filter(uid=request.user.id)
    orderid = random.randrange(1000, 9999)
    for x in c:
        amount = x.qty * x.pid.price
        o = Order.objects.create(orderid=orderid, pid=x.pid, uid=x.uid,
                                 qty=x.qty, amt=amount)
        o.save()
        x.delete()
    return redirect('/fetchorder')


def fetchorder(request):
    o = Order.objects.filter(uid=request.user.id)
    context = {'data': o}
    sum = 0
    for x in o:
        sum = sum + x.amt
    context['total'] = sum
    context['n'] = len(o)

    orders_to_delete = list(o)
    for order in orders_to_delete:
        Orderhistory.objects.create(order=order, payment_status='successful')

    return render(request, 'placeorder.html', context)


def sortbyprice(request, sv):
    if sv == '1':
        p = Product.objects.order_by('price')  # descending order
    else:
        p = Product.objects.order_by('-price')  # ascending order
    context = {}
    context['data'] = p
    return render(request, 'index.html', context)


def pricefilter(request):
    min = request.GET['min']
    max = request.GET['max']
    q1 = Q(price__gte=min)  # price>=0
    q2 = Q(price__lte=max)  # price<=100
    q3 = Q(is_active=True)
    p = Product.objects.filter(q1 & q2 & q3)
    context = {}
    context['data'] = p
    return render(request, 'index.html', context)


def catfilter(request, cv):  # cv-category value
    q1 = Q(is_active=True)  # Q- it is used for defining the conditions
    q2 = Q(cat=cv)
    p = Product.objects.filter(q1 & q2)  # q1 and q2 are conditions.
    print(p)
    context = {}
    context['data'] = p
    return render(request, 'index.html', context)


def updateqty(request, x, cid):
    c = Cart.objects.filter(id=cid)
    q = c[0].qty
    if x == '1':
        q = q + 1
    elif q > 1:
        q = q - 1
    c.update(qty=q)
    return redirect('/viewcart')


def search(request):
    query = request.GET['query']
    pname = Product.objects.filter(name__icontains=query)
    pcat = Product.objects.filter(cat__icontains=query)
    pdetail = Product.objects.filter(pdetail__icontains=query)
    allprod = pname.union(pcat, pdetail)
    context = {}
    if allprod.count() == 0:
        context['errmsg'] = 'Dog not Found'
    context['data'] = allprod
    return render(request, 'index.html', context)


def paymentsuccess(request):
    sub = 'SAM Dog Shop Order Status'
    msg = 'Thanks For Buying...!!'
    frm = 'ganeshpushpala23@gmail.com'
    u = User.objects.filter(id=request.user.id)
    to = u[0].email
    send_mail(
        sub,
        msg,
        frm,
        [to],
        fail_silently=False
    )
    return render(request, 'paymentsuccess.html')


def makepayment(request):
    client = razorpay.Client(auth=('rzp_test_g6ojiwK9Ofsbj4', '4pxP9iEnsMFbNL8kday7xHU6'))
    o = Order.objects.filter(uid=request.user.id)
    sum = 0
    for x in o:
        sum = sum + x.amt
        oid = x.orderid

    data = {'amount': sum * 100, 'currency': 'INR', 'receipt': "oid"}
    payment = client.order.create(data=data)
    context = {}
    context['payment'] = payment
    return render(request, 'pay.html',context)
