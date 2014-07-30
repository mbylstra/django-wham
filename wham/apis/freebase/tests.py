import json
from os.path import dirname, join
from django.test import TestCase
from wham.httmock import urlmatch, HTTMock
from requests import HTTPError
from wham.apis.freebase.models import FreebaseMusicbrainzArtist
import os

APP_DIR = os.path.dirname(__file__)
MOCK_RESPONSES_DIR = join(APP_DIR, 'mock_responses')


# mock_functions = build_httmock_functions(MOCK_RESPONSES_DIR)

class TestCase(TestCase):

    def setUp(self):
        pass

    def test_musicbrainz(self):
        # with HTTMock(*mock_functions):

        ids = [
            '482c09c0-fe65-424f-b9e7-9ec08a999a2f',
            '6ac67c73-2833-4af3-b2e7-3bec5a7e3f85',
            'b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d',
            'f2492c31-54a8-4347-a1fc-f81f72873bbf',
            '5f3c98a5-8cda-4a1e-a8f8-c41aab636b97',
            '4c48078c-af4e-4ca3-9838-5841d91826e1',
            '859d4c71-8baf-4987-91ac-a138c9bba81f',
            '6dd52e57-52a7-4618-972c-4f0de3dbcadf',
            '157aed6f-e861-4649-b838-41d11c2e5f0a',
            '0ef5eb85-fddb-443b-8a14-8b5da90be3e9',
            '3ff72a59-f39d-411d-9f93-2d4a86413013',
            'adec1fc3-83c1-48f7-9e49-8347ac6d40b0',
            'd98c8149-0c01-4151-93e1-48fdc3d5027f',
            'c2f0fb92-4e5d-4136-97d9-043e10ee1154',
            'cee3f961-4197-483b-a3ad-73242a97eb4a',
            '541bacd0-6aeb-4292-8d3a-882e85519953',
            '2f24f70e-c1ce-4fd4-a927-48fad3fe74e0',
            '8475297d-fb78-4630-8d74-9b87b6bb7cc8',
            '61dd30be-8e7b-4c85-9aa4-be66702c4644',
            '1cf5f079-706d-4b1f-9de9-0bf8e298cc97',
            '6c4faf49-a133-4465-a97d-6c68c52ad88b',
            '582748ae-a993-4b14-a2be-199fe8f418e6',
            '65cc77e1-45cf-4c2a-958c-c7cca472970c',
            '98e4bf9e-9e33-4f07-9962-f7c1c2d773ba',
            '93eb7110-0bc9-4d3f-816b-4b52ef982ec8',
            '8ca01f46-53ac-4af2-8516-55a909c0905e',
            '2819834e-4e08-47b0-a2c4-b7672318e8f0',
            'd5cc67b8-1cc4-453b-96e8-44487acdebea',
            '9a6880e7-5795-4ed3-8c58-7fef968aaa61',
            '31e9c35b-2675-4632-8596-f9bd9286f6c8',
            '2dea8a55-623b-42bb-bda3-9fb784018b40',
            '2c1bc1cb-4ae8-427b-ba28-4a695e47388f',
            '0c502791-4ee9-4c5f-9696-0602b721ff3b',
            '5c9fefe7-7bbb-47f8-b54e-9b5361beed5c',
            '6821bf3f-5d5b-4b0f-8fa4-79d2ab2d9219',
            'c213f661-70a8-42aa-b858-62f5bd2d72e9',
            'e9fcd661-cf2f-4792-aa50-364e1a576ac3',
            '3a6d6481-142d-423f-91d4-55bbfff318ed',
            '0d8303d1-6653-43f1-a0ef-2fcd3835529f',
            '2af759f4-4c48-49eb-a512-ae463c40b99a',
            '1d45138d-c675-4016-87a7-7ad5cce5e1bc',
            '4e442c83-b547-4d6e-9270-cdd35e3c3195',
            '5b8a28ee-dc6b-48db-ae98-f4ef1f15ae6d',
            '18dc6bd7-9caa-4c2d-a2fc-e9546ebda6a4',
            '0e23b5e8-0f99-45f4-bb2d-a266d65f13f3',
            '381e8434-109a-439c-8acc-5d328359f2e0',
            '26fe7532-dc1e-45d1-bfcb-a7f83d4df98e',
        ]
        for id in ids:
            print '===================================================='
            try:
                artist = FreebaseMusicbrainzArtist.objects.get(pk=id)
                print artist.name
                print '---------------------------------------------------'
                if artist.origin_text:
                    print artist.origin_text
                if artist.place_of_birth:
                    print artist.place_of_birth
            except HTTPError:
                print 'could not find musicbrainz id'
