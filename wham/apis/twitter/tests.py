import json
from os.path import dirname, join
from django.test import TestCase
from wham.httmock import urlmatch, HTTMock
from wham.apis.twitter.models import Tweet, TwitterUser
import os
from wham.tests import build_httmock_functions

APP_DIR = os.path.dirname(__file__)
MOCK_RESPONSES_DIR = join(APP_DIR, 'mock_responses')


mock_functions = build_httmock_functions(MOCK_RESPONSES_DIR)

class TestCase(TestCase):

    def setUp(self):
        pass

    def test_twitter(self):
        with HTTMock(*mock_functions):
            user = TwitterUser.objects.get(pk='795649')

            tweet = Tweet.objects.get(pk=210462857140252672)
            self.assertEquals(tweet.text, "Along with our new #Twitterbird, we've also updated our Display Guidelines: https://t.co/Ed4omjYs  ^JC")
            self.assertEquals(tweet.retweet_count, 74)

            tweets = user.tweets.all()
            self.assertEqual(tweets.count(), 35)

            tweets = user.tweets.all()
            self.assertEqual(tweets.count(), 35) #this time we should get the cached version...  how can we test this though?
                    #perhaps by keeping a history of what happened? At least this tests that getting the cached version doesn't break

            tweets = user.tweets.all(wham_fetch_live=True)
            self.assertEqual(tweets.count(), 35)


            user = TwitterUser.objects.get(screen_name='rsarver')
            self.assertEqual(TwitterUser.objects.count(), 1)
            self.assertEqual(user.pk, 795649)
            self.assertEqual(TwitterUser.objects.get(screen_name='rsarver', wham_fetch_live=True) \
                                .tweets.all(wham_fetch_live=True).order_by('-retweet_count')[0].retweet_count,
                             289)


            neckbeardhacker = TwitterUser.objects.get(screen_name='NeckbeardHacker') #has 415 tweets
            tweets = neckbeardhacker.tweets.all(wham_pages=5) #the fifth page is the last page (just has last_id)
