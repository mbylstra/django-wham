from django.db import models
from wham.apis.deezer.models import DeezerTrack, DeezerArtist
from wham.apis.spotify.models import SpotifyTrack, SpotifyArtist


class SpotifyDeezerTrackMatch(models.Model):
    deezer = models.OneToOneField(DeezerTrack, related_name='spotify_match')
    spotify = models.OneToOneField(SpotifyTrack, related_name='deezer_match')

    class Meta:
        db_table = 'spotify_deezer_track_match'


class ArtistManager(models.Manager):

    def match_deezer_artist(self, spotify_artist):
        try:
            #get the cached match
            return self.model.objects.get(spotify_artist=spotify_artist).spotify_artist
        except self.model.DoesNotExist:
            #try to match
            for potential_artist in DeezerArtist.objects.filter(name__icontains=spotify_artist.name):
                if potential_artist.name == spotify_artist.name:
                    deezer_artist = potential_artist
                    self.model.objects.create(
                        spotify_artist=spotify_artist,
                        deezer_artist=deezer_artist,
                    )
                    return deezer_artist
            return None #TODO: this should be stored in the database


    def match_spotify_artist(self, deezer_artist):
        pass

class SpotifyDeezerArtistMatch(models.Model):
    objects = ArtistManager()
    deezer_artist = models.OneToOneField(DeezerArtist, related_name='spotify_match')
    spotify_artist = models.OneToOneField(SpotifyArtist, related_name='deezer_match')

    class Meta:
        db_table = 'spotify_deezer_artist_match'

