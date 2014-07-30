from django.db import models

# Create your models here.
from wham.fields import WhamTextField, WhamCharField
from wham.models import WhamModel


class FreebaseMeta:
    base_url = 'https://www.googleapis.com/freebase/v1/'


class Person(WhamModel):

    id = models.CharField(max_length=255, primary_key=True)
    name = WhamTextField()

    class WhamMeta(FreebaseMeta):
        endpoint = 'topic'


class ProgrammingLanguage(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField(
        wham_result_path=('property', '/type/object/name', 'values', 0, 'value')
    )
    # language_designers = models.ManyToManyField('Person')

    class WhamMeta(FreebaseMeta):
        endpoint = 'topic'

    def __unicode__(self):
        return self.name


# class FreebaseMusicArtist(WhamModel):
#     objects = WhamManager()
#     id = WhamCharField(max_length=255, primary_key=True)
#     musicbrainz_id = WhamCharField(max_length=255, unique=True, wham_can_lookup=True)


# this is a copout having separate models for music/artist and authority/musicbrainz/artist as
# I don't know how to deal with namespaces yet!
class FreebaseMusicbrainzArtist(WhamModel):

    id = WhamCharField(max_length=255, primary_key=True)
    name = WhamTextField(
        wham_result_path=('property', '/type/object/name', 'values', 0, 'value')
    )
    origin_text = WhamTextField(
        wham_result_path=('property', '/music/artist/origin', 'values', 0, 'text')
    )
    place_of_birth = WhamTextField(
        wham_result_path=('property', '/people/person/place_of_birth', 'values', 0, 'text')
    )

    class WhamMeta(FreebaseMeta):
        endpoint = 'topic/authority/musicbrainz/artist'


# country/place for band is in:
#   /music/artist/origin
# country/place for solo performer is

#/people/person/place_of_birth

# also of use (solo artist)
# /music/artist/active_end: {},
# /music/artist/active_start: {},
# /music/artist/album: {},
# /music/artist/contribution: {},
# /music/artist/genre: {},
# /music/artist/track: {},
# /music/artist/track_contributions: {},

#(band stuff)
# /music/artist/active_end: {},
# /music/artist/active_start: {},
# /music/artist/album: {},
# /music/artist/concert_tours: {},
# /music/artist/genre: {},
# /music/artist/home_page: {},
# /music/artist/label: {},
# /music/artist/origin: {},
# /music/artist/track: {},
# /music/musical_group/member: {},