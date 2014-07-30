from django.db import models
from wham.fields import WhamTextField, WhamIntegerField, WhamFloatField, \
    WhamCharField
from wham.models import WhamModel


class DeezerMeta:
    base_url = 'http://api.deezer.com/'
    # pk_property = 'id'

class DeezerTrack(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    title = WhamTextField() #TODO: this shouldn't be required if json property is same as django fieldname

    rank = WhamIntegerField(null=True)
    bpm = WhamFloatField(null=True)
    track_position = WhamIntegerField(null=True)

    # examples:
    # id: 3135556,
    # readable: true,
    # title: "Harder Better Faster Stronger",
    # isrc: "GBDUW0000059",
    # link: "http://www.deezer.com/track/3135556",
    # duration: 225,
    # track_position: 4,
    # disk_number: 1,
    # rank: 757802,
    # explicit_lyrics: false,
    # preview: "http://cdn-preview-5.deezer.com/stream/51afcde9f56a132096c0496cc95eb24b-3.mp3",
    # bpm: 123.5,
    # gain: -6.48,
    # available_countries: [],
    # artist: {},
    # album: {},
    # type: "track"

    class Meta:
        db_table = 'deezer_track'

    class WhamMeta(DeezerMeta):
        endpoint = 'track'

        # does not currently work as Wham search is currently limited to name__icontains #TODO
        # class Search:
        #     endpoint = 'search/track'
        #     results_path = ('data',)
        #     fields = ('title',) #actually only uses one for now

    def __unicode__(self):
        return self.title
