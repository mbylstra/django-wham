from os.path import join
import os
from django.test import TestCase
from wham.apis.instagram.models import InstagramTag, InstagramPost

class TestCase(TestCase):

    def test_instagram(self):

        for post in InstagramTag.objects.get(id='pyconau').posts.all():
            print post
            # display(Image(post.image_url))

