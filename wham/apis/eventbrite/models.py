from django.db import models

# Create your models here.
from wham.fields import WhamCharField, WhamTextField, WhamIntegerField, \
    WhamManyToManyField, WhamFloatField, WhamForeignKey
from wham.models import WhamModel


class EventbriteMeta:
    base_url = 'https://www.eventbriteapi.com/v3/'
    requires_oauth_token = True


class EventbriteVenue(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField()
    latitude = WhamFloatField()
    longitude = WhamFloatField()

    city = WhamTextField(wham_result_path=('address', 'city'), null=True)
    country = WhamTextField(wham_result_path=('address', 'country'), null=True)
    region = WhamTextField(wham_result_path=('address', 'region'), null=True)
    address_1 = WhamTextField(wham_result_path=('address', 'address_1'), null=True)
    address_2 = WhamTextField(wham_result_path=('address', 'address_2'), null=True)
    country_name = WhamTextField(wham_result_path=('address', 'country_name'), null=True)

    class Meta:
        db_table = 'eventbrite_venue'

    def __unicode__(self):
        return self.name


class EventbriteEvent(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField(wham_result_path=('name', 'text'))
    resource_uri = WhamTextField()
    url = WhamTextField()
    capacity = WhamIntegerField()
    venue = WhamForeignKey(EventbriteVenue, null=True) #this should be a foreign key! But we only support m2m so far.


    class WhamMeta(EventbriteMeta):
        endpoint = 'events'

        class Search:
            endpoint = 'events/search'
            results_path = ('events',)

    class Meta:
        db_table = 'eventbrite_event'

    def __unicode__(self):
        return self.name

