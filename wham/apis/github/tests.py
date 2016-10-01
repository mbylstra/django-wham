from os.path import join
from django.test import TestCase
from django.test.utils import override_settings

from wham.apis.github.models import Repository
from wham.httmock import HTTMock
import os
from wham.apis.lastfm.models import LastFmUser, LastFmArtist, LastFmUserTopArtists
from wham.tests import build_httmock_functions

APP_DIR = os.path.dirname(__file__)
MOCK_RESPONSES_DIR = join(APP_DIR, 'mock_responses')


mock_functions = build_httmock_functions(MOCK_RESPONSES_DIR)



class TestCase(TestCase):

    # @override_settings(LASTFM_API_KEY='a04961fe4330211ff149a949dfabef51')
    def test_github(self):
        repositories = Repository.objects.wham_filter(language="Elm")
        for repo in repositories:
            print repo.name
            print repo.stargazers_count
        # Repository.objects.filter(

        # with HTTMock(*mock_functions):
            # user = LastFmUser.objects.wham_get(pk='CarpetSquare')
            # self.assertEquals(user.name, 'CarpetSquare')
            #
            # artists = user.top_artists.wham_all()
            # top_artist = artists[0]
            # self.assertEqual(top_artist.name, "Ariel Pink's Haunted Graffiti")


            # the_beatles = LastFmArtist.objects.wham_get(pk='the beatles')
            # self.assertEqual


            # top_artist_through = LastFmUserTopArtists.objects.wham_get(user=user, artist=top_artist)
            # self.assertEqual(top_artist_through.playcount, "224")
            # for artist in artists:
            #     print artist.mbid
