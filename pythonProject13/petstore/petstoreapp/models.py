from django.db import models


# Create your models here.
class Contactenquiry(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=60)
    message = models.TextField()


class Product(models.Model):
    objects = None
    CAT = ((1, 'Beagle'),
           (2, 'Bulldog'),
           (3, 'German Shepherd'),
           (4, 'Poodle'),
           (5, 'English Springer Spaniel'),
           (6, 'Airedale Terrier'))
    name = models.CharField(max_length=50, verbose_name='Product Name')
    price = models.FloatField()
    age = models.IntegerField()
    cat = models.IntegerField(verbose_name='Category', choices=CAT)
    pdetail = models.TextField(max_length=300, verbose_name='Product Details')
    is_active = models.BooleanField(default=True)
    pimage = models.ImageField(upload_to='image')

    def _str_(self):
        return self.name


class Cart(models.Model):
    objects = None
    uid = models.ForeignKey('auth.user', on_delete=models.CASCADE, db_column='uid')
    pid = models.ForeignKey('Product', on_delete=models.CASCADE, db_column='pid')
    qty = models.IntegerField(default=1)


class Order(models.Model):
    objects = None
    orderid = models.IntegerField()
    uid = models.ForeignKey('auth.user', on_delete=models.CASCADE, db_column='uid')
    pid = models.ForeignKey('Product', on_delete=models.CASCADE, db_column='pid')
    qty = models.IntegerField(default=1)
    amt = models.FloatField()


class Orderhistory(models.Model):
    objects = None
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)