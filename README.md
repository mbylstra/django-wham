django-wham
===========
**REST APIs disguised as Django ORM Models**


With django-wham you can query REST APIs in exactly the same way you query Django Models:


```
>>> artist = SpotifyArtist.objects.get(id='5Z1XZyEFY0dewG8faEIiEx')
fetching https://api.spotify.com/v1/artists/5Z1XZyEFY0dewG8faEIiEx
>>> print artist.name
Django Reinhardt
```

```
>>> twitter_user = TwitterUser.objects.get(screen_name='djangoproject')
fetching https://api.twitter.com/1.1/users/show.json?screen_name=djangoproject
>>> for tweet in twitter_user.tweets.all():
>>>     print tweet.text
fetching https://api.twitter.com/1.1/statuses/user_timeline.json?user_id=191225303
Django 1.7 release candidate 2 - It's almost here! Today we're pleased to announce the second release-candidate pa...
Django 1.7 release candidate 1 - It's almost here! Tonight we're pleased to announce the first release-candidate p...
...
```

### Creating Django Wham Models

In order to query a REST API (eg: Twitter, Flickr, Youtube, etc), you need a Wham Model. A Wham Model corresponds to an API Endpoint and has a special inner WhamMeta class that describes how the REST API should map to the Django Model.


This simple Wham Model that enables you too look up a Spotify Artist by its Spotify ID and retrieve some information about that artist.
In this case the names of the fields match the property names of the retrieved JSON data, so very little configuration is required.

```
from wham.models import WhamModel

class SpotifyArtist(WhamModel):

    id = CharField(max_length=100, primary_key=True) 
        # the primary key field should be of the same name and type as the API Endpoint ID
        # rather than the default auto-incrementing key Django provides. For example,
        # '5Z1XZyEFY0dewG8faEIiEx' is the Spotify ID for Django Reinhardt.
    name = TextField()
    href = TextField()
    popularity = IntegerField()
    uri = UriField()

    class WhamMeta(SpotifyMeta):
        base_url = 'https://api.spotify.com/v1/'
        endpoint = 'artists'
```

Now we add another Spotify Endpoint, this time both of the Models' WhamMeta class inherit from a single class,
to share commonalities between endpoints such as the base url
```
class SpotifyWhamMeta:
    base_url = 'https://api.spotify.com/v1/'

class SpotifyArtist(WhamModel):
    ...
    
    class WhamMeta(SpotifyWhamMeta):
        endpoint = 'artists'

class SpotifyAlbum(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField()
    release_date = WhamTextField(null=True)
    popularity = WhamIntegerField(null=True, wham_detailed=True)

    class WhamMeta(SpotifyWhamMeta):
        endpoint = 'albums'

```

### Many To Many Endpoints

Django Wham supports many to many endpoints such as `https://api.spotify.com/v1/artists/{id}/albums`.
This is possible by specifying a WhamManyToMany field and doing a little configuration.

To create a many to many field between Artists and Albums:

```
class SpotifyArtist(WhamModel):
    ...
    
    albums = WhamManyToManyField(
        'SpotifyAlbum',
        wham_endpoint='artists/{{id}}/albums', #django template syntax is used to substitue the value of thd id
        wham_results_path=['items'] 
            # This is the 'path' where to find the list of results in the retreived JSON data.
            # The list or tuple represents a path in the JSON tree. A hypothetical example might be ['photos', 'results']
    )
    
    ...

```


### Wham Model Repository

Have a look at https://github.com/mbylstra/django-wham/tree/master/wham/apis for some more examples of Wham Models. We're hoping this will become an ever growing repository of Wham Models for the multitude of public REST APIs on the web, so you won't have to write your own. If you have ever wanted to contribute to open source, but have been too daunted, creating a Wham Model is a fun and easy way to get started. Only basic Django experience is required.

### Installation and use of Wham Models


django-wham can be installed via PyPI:
```
    pip install django-wham

```

Add some entries to your INSTALLED_APPS in your settings.py file. See https://github.com/mbylstra/django-wham/tree/master/wham/apis for a list of example apis.
```
INSTALLED_APPS = (
    ...
    'wham', #required
    'wham.apis.spotify', #an optional provided API
    'wham.apis.twitter', #optional
    'your_custom_wham_app' #this should be a Django app with one or more Wham Models in its models.py file
    ...
)

```
You must then run syncdb before you can start using any wham models
```
python manage.py syncdb

```
Django wham models can be used just like regular Django Models
```
from wham.apis.spotify import SpotifyArtist
SpotifyArtist.objects.filter(name__icontains="green")
```

### demo

This git repository also comes with a demo django project and some Ipython notebook examples that can be run with `django manage.py shell_plus --notebook`. Your environment must have the packages in ipython-requirements.txt installed for this to work. 


### More Info
- [here are some slides about django-wham](http://slides.com/mbylstra/django-wham)

### Disclaimer
_Django Wham is currently in an Alpha/Proof-of-Concept stage. While I am using it to great success in my project http://kaleidoscope.fm, there are probably many edge cases that it does not handle very well. I would not recommend using this in production just yet. If you are interested in using this, please contact me and I won't hestitate to help out. Any kind of feedback would also be highly appreciated (bug reports, suggestions for improvements, requests for more APIs to be supported) - please submit a Git issue!_
