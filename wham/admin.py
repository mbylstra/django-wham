from django.contrib import admin

# Register your models here.



from django.contrib import admin

from wham.models import RateLimitingData

admin.site.register(RateLimitingData)
