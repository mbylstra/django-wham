from os.path import join
import os
from django.test import TestCase
from wham.apis.deezer.models import DeezerTrack

class TestCase(TestCase):

    def test_deezer(self):
        track = DeezerTrack.objects.get(id='3135556')
        print track
        track = DeezerTrack.objects.get(pk='3135556')
        print track

        # not currently working
        # track = DeezerTrack.objects.get(id='3135556') #we should definitely support id as well as pk
        # for track in DeezerTrack.objects.filter(title__icontains='django').order_by('bpm'):
        #     print track

