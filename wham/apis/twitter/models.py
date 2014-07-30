from django.db import models

# Create your models here.
from django.template.loader import render_to_string
from wham.fields import WhamIntegerField, WhamTextField, WhamManyToManyField, \
    WhamDateTimeField
from wham.models import FROM_LAST_ID, WhamModel


CREATED_AT_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'

class TwitterMeta:
    base_url = 'https://api.twitter.com/1.1/'
    auth_for_public_get = 'TWITTER' #this needs to be abstracted more
    url_postfix = '.json'
    pager_param = 'max_id'
    pager_type = FROM_LAST_ID


class TwitterUser(WhamModel):

    id = WhamIntegerField(primary_key=True)
    text = WhamTextField()

    screen_name = WhamTextField(unique=True, wham_can_lookup=True)

    #this is dodgy, because this should really be a oneToMany field which you have
    # to specify as a FK on the other model (which can be annoying!)
    tweets = WhamManyToManyField(
        #https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=twitterapi&count=2
        # user_id=23234
        'Tweet',
        related_name='users',
        wham_endpoint='statuses/user_timeline',
        wham_pk_param='user_id',
        wham_params = {
            'count': 200,
            'exclude_replies': 'true',
            'include_rts': 'false',
        }
    )

    class Meta:
        db_table = 'twitter_user'

    class WhamMeta(TwitterMeta):
        endpoint = 'users/show'
        url_pk_type = 'querystring'
        url_pk_param = 'user_id'

        #https://api.twitter.com/1.1/users/show.json?screen_name=rsarver

    def __unicode__(self):
        return self.screen_name

# https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=twitterapi&count=2

# https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=twitterapi&count=2

class Tweet(WhamModel):

    id = WhamIntegerField(primary_key=True)
    text = WhamTextField()
    created_at = WhamDateTimeField(wham_format=CREATED_AT_FORMAT)

    retweet_count = WhamIntegerField(null=True)
    favourites_count = WhamIntegerField(null=True)

    class Meta():
        ordering = ('-created_at',)

    class WhamMeta(TwitterMeta):
        endpoint = 'statuses/show'

    def __unicode__(self):
        return self.text

    def _repr_html_(self):
        return render_to_string('wham/twitter/ipython_notebook/tweet.html', {'tweet': self})



