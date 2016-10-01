from django.conf.urls import url
# from django.contrib import admin
# admin.autodiscover()
import views

urlpatterns = [
    # Examples:
    url(r'^$', views.home, name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^admin/', include(admin.site.urls)),
]
