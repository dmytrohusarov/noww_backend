from django.db import models
from django.utils import timezone
from django.db.models import Avg, F, Sum
from django.core.validators import RegexValidator
from django_countries.fields import CountryField
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import User as BaseUser, PermissionsMixin

from .managers import UserManager
from rest_framework.authtoken.models import Token
from djmoney.models.fields import MoneyField

from nowwapi.utils import GoogleBucketUrlField
from noww.Handlers.TokenHandler import OrderRequest


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()
    avatar_url = GoogleBucketUrlField(blank=True, null=True)
    email = models.EmailField(('email address'), blank=True)
    first_name = models.CharField(('first name'), max_length=30, blank=True)
    last_name = models.CharField(('last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(('date joined'), auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(('active'), default=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    password = models.CharField(max_length=50)
    is_superuser = models.BooleanField(('is_superuser'), default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['is_staff']

    # this methods are require to login super user from admin panel
    def has_perm(self, perm, obj=None):
        return self.is_staff

    # this methods are require to login super user from admin panel
    def has_module_perms(self, app_label):
        return self.is_staff

    class Meta:
        verbose_name = ('user')
        verbose_name_plural = ('users')


class Worker(models.Model):
    user = models.OneToOneField('noww.User', on_delete=models.CASCADE)
    created_by = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    device = models.CharField(('device'), max_length=200, blank=True)
    is_ready = models.BooleanField(default=False)
    status_description = models.CharField(max_length=256, blank=True)

    __verified = None

    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.__verified = self.is_verified

    def get_absolute_url(self):
        return "/api/workers/%i/" % self.id

    @property
    def rate(self):
        rate_ = self.worker_reviews.aggregate(Avg(F('review__star'))) \
            .get("review__star__avg")
        return rate_.__round__(2) if rate_ else None

    @property
    def profit(self):
        profit_ = self.tasks.aggregate(Sum(F('delivery_cost'))). \
            get('delivery_cost__sum')
        return profit_.__round__(2) if profit_ else None

    def get_current_tasks(self):
        current_tasks = self.tasks.filter(status__in=["CREATED"])
        return current_tasks

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        # get deafault system review
        # TODO: temporary HARDCODE in args
        def_review = Review.objects.filter(star=5, description='SYSTEM ITEM').first()
        if self.is_verified != self.__verified and self.is_verified is True:
            self.worker_reviews.create(
                worker_id=self.pk,
                review_id=def_review.pk
            )

        super(Worker, self).save(force_insert, force_update, *args, **kwargs)
        self.__verified = self.is_verified


class Address(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    address = models.CharField("Address line 1", max_length=1024)
    zip_code = models.CharField("ZIP / Postal code", max_length=12)
    city = models.CharField("City", max_length=1024)
    country = CountryField()


class Review(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(blank=True, null=True)
    star = models.PositiveSmallIntegerField(default=0)
    description = models.CharField(max_length=200, null=True, blank=True)
    customer = models.ForeignKey(
        "Customer", on_delete=models.CASCADE, blank=True, null=True,
        related_name="customers_reviews"
    )


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_by = models.CharField(max_length=50, blank=True, null=True)
    device = models.CharField(('device'), max_length=200, blank=True)
    addresses = models.ManyToManyField(
        Address, verbose_name="list of addresses"
    )
    default_address_id = models.IntegerField(default=0)

    @property
    def profit(self):
        profit_ = self.tasks.aggregate(Sum(F('delivery_cost'))). \
            get('delivery_cost__sum')
        return float(profit_).__round__(2) if profit_ else None


class CustomerReview(models.Model):
    worker = models.ForeignKey(
        'Worker', on_delete=models.CASCADE, blank=False, null=False,
        related_name='worker_reviews'
    )
    # TODO: maybe future
    place = models.ForeignKey(
        'Place', on_delete=models.CASCADE, blank=True, null=True,
        related_name='place_reviews'
    )
    review = models.ForeignKey(
        "Review", on_delete=models.CASCADE, blank=True, null=True,
        related_name="customer_review"
    )


class Service(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=50, blank=False)
    description = models.CharField(max_length=200)
    type = models.CharField(max_length=50, blank=False)


class Types(models.Model):
    """
        hierarchical class for types - kinds
        entities: places, products
    """
    created_at = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='parent_item', null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True, verbose_name="description")
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH')
    image_url = models.URLField(blank=True, null=True)
    kinds = models.ManyToManyField(Types, related_name="products_kinds")
    sub_kinds = models.ManyToManyField(Types, related_name="products_subkinds")
    places = models.ForeignKey(
        'Place', verbose_name="list of places", null=True,
        related_name='place_to_product', on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title


class Place(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=50, blank=False)
    description = models.TextField(blank=True, verbose_name="description")
    addresses = models.ManyToManyField(Address)
    image_url = models.URLField(blank=True, null=True)

    @property
    def kinds(self):
        kinds_ids = self.place_to_product.values_list('kinds', flat=True) \
            .distinct()
        kinds = Types.objects.filter(id__in=kinds_ids)
        return kinds

    @property
    def sub_kinds(self):
        kinds_ids = self.place_to_product.values_list('sub_kinds', flat=True) \
            .distinct()
        kinds = Types.objects.filter(id__in=kinds_ids)
        return kinds


class TaskItem(models.Model):
    task = models.ForeignKey('Task', on_delete=models.DO_NOTHING, related_name='task_to_product')
    product = models.ForeignKey('Product', on_delete=models.DO_NOTHING, related_name='product_to_task')
    quantity = models.CharField(max_length=200)


class Task(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=False, blank=False)
    updated_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default='CREATED')
    description = models.CharField(max_length=200)
    delivery_cost = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', null=True, blank=True)
    product_cost = MoneyField(max_digits=14, decimal_places=2, default_currency='UAH', null=True, blank=True)
    duration = models.IntegerField(null=True)
    title = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    weight = models.IntegerField(null=True)
    pay_type = models.CharField(max_length=50, default='CASH')

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, blank=True, null=True, related_name='tasks')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True, related_name='tasks')
    place = models.ForeignKey('Place', on_delete=models.CASCADE, null=True)
    task_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='task_address', null=True)
    customer_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='task_customer_address',
                                         null=True)
    items = models.ManyToManyField(Product, through=TaskItem)
    reject_code = models.CharField(max_length=50, blank=True, null=True)

    def get_total_money(self):
        return float(self.delivery_cost.amount + self.product_cost.amount)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            OrderRequest(lat=self.task_address.latitude, lon=self.task_address.longitude, task_id=self.pk)
        else:
            super().save(*args, **kwargs)


class Dictionary(models.Model):
    name = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=50, blank=True)
    value = models.TextField(blank=True)
    sequence = models.IntegerField(null=True)


class Doc(models.Model):
    url = GoogleBucketUrlField(blank=True, null=True)
    name = models.CharField(max_length=64, null=True)
    description = models.TextField(blank=True, null=True)
    worker = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name='docs'
    )
