from django.db import models
from wham.fields import WhamCharField, WhamTextField
from wham.models import WhamModel


class MusicbrainzMeta:
    base_url = 'http://musicbrainz.org/ws/2/'
    api_params = {'fmt': 'json'}


class MusicbrainzArtist(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField()
    country = WhamCharField(max_length=255, null=True)


    class WhamMeta(MusicbrainzMeta):
        endpoint = 'artist/'

    class Meta:
        db_table = 'musicbrainz_artist'

    def __unicode__(self):
        return self.name

