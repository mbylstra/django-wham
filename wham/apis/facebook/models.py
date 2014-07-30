# Create your models here.
from django.template.loader import render_to_string
from wham.fields import WhamCharField, WhamTextField
from wham.models import WhamModel


class FacebookMeta:
    base_url = 'https://graph.facebook.com/'
    requires_oauth_token = True

class FacebookUser(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    username = WhamTextField(unique=True)
    name = WhamTextField()
    gender = WhamTextField()
    first_name = WhamTextField()
    last_name = WhamTextField()

    class Meta:
        db_table = 'facebook_user'

    class WhamMeta(FacebookMeta):
        endpoint = ''

    def __unicode__(self):
        return self.name