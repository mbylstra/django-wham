from django.db import models

# Create your models here.

# http://api.soundcloud.com/tracks/13158665.json?client_id=a43d27e75fbd64533f57428dd7be3ba5

from django.db import models
from wham.fields import WhamTextField, WhamIntegerField
from wham.models import WhamModel


class SoundcloudMeta:
    base_url = 'http://api.soundcloud.com/'
    auth_for_public_get = 'API_KEY'
    api_key_settings_name = 'SOUNDCLOUD_CLIENT_ID'
    api_key_param = 'client_id'

class SoundcloudTrack(WhamModel):

    id = models.CharField(max_length=255, primary_key=True)
    title = WhamTextField()

    track_type = WhamTextField(null=True)
    stream_url = WhamTextField(null=True)
    playback_count = WhamIntegerField(null=True)

    class Meta:
        db_table = 'soundcloud_track'

    class WhamMeta(SoundcloudMeta):
        url_postfix = '.json'

        endpoint = 'tracks/'
        class Search:
            endpoint = 'tracks'
            fields = ('title',)


    def __unicode__(self):
        return self.title