from os.path import join
import os
from django.test import TestCase
from wham.httmock import HTTMock

from wham.apis.spotify.models import SpotifyTrack, SpotifyArtist
from wham.tests import build_httmock_functions

APP_DIR = os.path.dirname(__file__)
MOCK_RESPONSES_DIR = join(APP_DIR, 'mock_responses')

mock_functions = build_httmock_functions(MOCK_RESPONSES_DIR)

class TestCase(TestCase):

    def test_spotify(self):

        with HTTMock(*mock_functions):
            track = SpotifyTrack.objects.get(pk='0eGsygTp906u18L0Oimnem')
            self.assertEquals(track.name, 'Mr. Brightside')
            tracks = SpotifyTrack.objects.all(wham_use_cache=True)
            self.assertEqual(tracks.count(), 1)
            artists = SpotifyArtist.objects.all(wham_use_cache=True)
            self.assertEqual(artists.count(), 1)
            artist = artists[0]

            self.assertEqual(artist.name, 'The Killers')

            albums = artist.albums.all()
            self.assertEqual(albums.count(), 20)

            albums = artist.albums.all() #this time it should get results from the database/cache (and not break)
            self.assertEqual(albums.count(), 20)

            albums = artist.albums.all(wham_depth=2) #this time it should make a full request for each album
            self.assertIsNotNone(albums[0].popularity) #popularity should have been gotten because of depth=2

            artists = SpotifyArtist.objects.filter(name__icontains='Django')
            self.assertEqual(artists[0].name, 'Django Reinhardt')
            artists = SpotifyArtist.objects.filter(name__icontains='Django') #this time get from cache



