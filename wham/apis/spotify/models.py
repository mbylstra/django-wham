from django.db import models

# Create your models here.
from wham.fields import WhamCharField, WhamTextField, WhamIntegerField, \
    WhamManyToManyField
from wham.models import WhamModel


class SpotifyMeta:
    base_url = 'https://api.spotify.com/v1/'


class SpotifyTrack(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField()

    href = WhamTextField(null=True)
    popularity = WhamIntegerField(null=True)
    track_number = WhamIntegerField(null=True)
    uri = WhamTextField(null=True)
    type = WhamTextField(null=True)
    preview_url = WhamTextField(null=True)
    artists = WhamManyToManyField('SpotifyArtist', related_name='tracks')

    class WhamMeta(SpotifyMeta):
        endpoint = 'tracks'

        class Search:
            endpoint = 'search'
            params = {'type': 'track'}
            results_path = ('tracks', 'items')

    class Meta:
        db_table = 'spotify_track'

    def __unicode__(self):
        return self.name


class SpotifyArtist(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField()

    href = WhamTextField(null=True)
    popularity = WhamIntegerField(null=True)
    uri = WhamTextField(null=True)

    albums = WhamManyToManyField(
        'SpotifyAlbum',
        related_name='artists',
        wham_endpoint='artists/{{id}}/albums',
        wham_results_path=('items',)
    )

    # TODO:
    # tracks = WhamManyToManyField(
    #     'SpotifyTrack',
    #     # related_name='artists',
    #     wham_endpoint='artists/{{id}}/albums',
    #     wham_results_path=('items',)
    # )

    class Meta:
        db_table = 'spotify_artist'

    class WhamMeta(SpotifyMeta):
        endpoint = 'artists'

        # i reckon this stuff should really be in Manager, as it has more to do with filter()
        # which is a Manager method

        class Search:
            endpoint = 'search'
            params = {'type': 'artist'}
            results_path = ('artists', 'items')

    def __unicode__(self):
        return self.name


class SpotifyAlbum(WhamModel):

    # objects = WhamManager()

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField()

    release_date = WhamTextField(null=True)
    popularity = WhamIntegerField(null=True, wham_detailed=True)

    class Meta:
        db_table = 'spotify_album'

    class WhamMeta(SpotifyMeta):
        endpoint = 'albums'
        # search_endpoint = 'search'
        # search_extra_params = {'type': 'album'}
        # search_results_path = ('albums', 'items')


    def __unicode__(self):
        return self.name

#how do we get an artists albums?

