from django.contrib import admin
from django.urls import path , include
from django.conf.urls.static import static
from django.conf import settings
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('' ,  RedirectView.as_view(url="/dashboard/" , permanent =False)) ,
    path('dashboard/' , include('dashboard.urls')) ,
    # path('mainform', views.mainform, name='mainform'),
] + static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)
