from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import RedirectView
from noww.viewsets import (
    WorkersViewSet, CustomersViewSet, ServicesViewSet, TasksViewSet,
    PlaceViewSet, UserViewSet, ReviewViewSet, ProductViewSet, TypeViewSet,
    AddressViewSet
)
from noww.Handlers.TokenHandler import TaskHandler

from rest_framework import routers
from django.utils.inspect import get_func_args

from noww.views import CustomAuthToken, ImageViewSet, AccessGroupView, \
    UserGroupAccess
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="NOWW API",
      default_version='v1',
      description="API methods for the interaction of mobile applications and "
                  "the admin Support panel",
      terms_of_service="https://link/to/terms/",
      contact=openapi.Contact(email="contact@noww.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


def _basename_or_base_name(basename):
    # freaking DRF... TODO: remove when dropping support for DRF 3.8
    if 'basename' in get_func_args(routers.BaseRouter.register):
        return {'basename': basename}
    else:
        return {'base_name': basename}


router = routers.DefaultRouter()
router.register(r'workers', WorkersViewSet, 'Workers')
router.register(r'customers', CustomersViewSet, 'Customers')
router.register(r'services', ServicesViewSet, 'Services')
router.register(r'tasks', TasksViewSet, base_name='Task')
router.register(r'places', PlaceViewSet, 'Places')
router.register(r'users', UserViewSet, 'User')
router.register(r'products', ProductViewSet, 'Product')
router.register(r'types', TypeViewSet, 'Type')
router.register(r'addresses', AddressViewSet, 'Address')
router.register(r'review', ReviewViewSet, 'Review')


urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/swagger/', permanent=False), name='index'),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('api/', include(router.urls)),
    url(r'^admin/', admin.site.urls),

    path('api/admin_report/', include('admin_reports.urls', namespace='admin_reports')),

    url(r'^api/login/', CustomAuthToken.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^api/order/task', TaskHandler.as_view()),
    url(r'^api/order/task/(?P<task_id>\d+)/$', TaskHandler.as_view(), name='task_update'),

    url(r'^api/upload/', ImageViewSet.as_view(), name='upload'),
    path('api/access_group/', AccessGroupView.as_view(), name='access_group'),
    path('api/access_group/<int:user_id>/', UserGroupAccess.as_view(),
         name='user_access_group')
]
