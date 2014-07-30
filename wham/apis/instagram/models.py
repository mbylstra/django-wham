from django.db import models


# https://api.instagram.com/v1/tags/djangocon/media/recent?client_id=c3cdcbff22f649f1a08bedf12be1ca86

from django.db import models
from wham.fields import WhamCharField, WhamManyToManyField, WhamImageUrlField
from wham.models import WhamModel


class InstagramMeta:
    base_url = 'https://api.instagram.com/v1/'
    auth_for_public_get = 'API_KEY'
    api_key_settings_name = 'INSTAGRAM_CLIENT_ID'
    api_key_param = 'client_id'

class InstagramTag(WhamModel):

    name = WhamCharField(max_length=255, primary_key=True)

    posts = WhamManyToManyField(
        #  https://api.instagram.com/v1/tags/djangocon/media/recent
        'InstagramPost',
        related_name='tags',
        wham_endpoint='tags/{{id}}/media/recent',
        wham_results_path=('data',)
    )

    class Meta:
        db_table = 'instagram_tag'

    class WhamMeta(InstagramMeta):
        endpoint = 'tags'
        detail_base_result_path = ('data',) #can we make this less verbose??

    def __unicode__(self):
        return self.name

class InstagramPost(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)

    type = WhamCharField(max_length=10)
    image_url = WhamImageUrlField(wham_result_path=('images', 'standard_resolution', 'url'))

    class Meta:
        db_table = 'instagram_media'

    class WhamMeta(InstagramMeta):

        class Search:
            endpoint = 'tags/{{tag}}/media/recent'
            results_path = ('data',)
            fields = ('tag',)

    def __unicode__(self):
        return self.image_url