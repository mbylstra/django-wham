from os.path import join
from django.test import TestCase
from httmock import HTTMock
import os
from wham.apis.lastfm.models import LastFmUser, LastFmUserTopArtists
from wham.tests import build_httmock_functions

APP_DIR = os.path.dirname(__file__)
MOCK_RESPONSES_DIR = join(APP_DIR, 'mock_responses')


mock_functions = build_httmock_functions(MOCK_RESPONSES_DIR)



class TestCase(TestCase):

    def setUp(self):
        pass

    def test_lastfm(self):

        with HTTMock(*mock_functions):
            user = LastFmUser.objects.get(pk='CarpetSquare')
            self.assertEquals(user.name, 'CarpetSquare')

            artists = user.top_artists.all()
            top_artist = artists[0]
            self.assertEqual(top_artist.name, "Ariel Pink's Haunted Graffiti")
            top_artist_through = LastFmUserTopArtists.objects.get(user=user, artist=top_artist)
            self.assertEqual(top_artist_through.playcount, "224")
            for artist in artists:
                print artist.mbid
