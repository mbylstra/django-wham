# -*- coding: utf-8 -*-
from copy import deepcopy
from urllib import urlencode

from django.conf import settings
from django.db.models import ForeignKey
from django.template import Template, Context
from django.template.loader import render_to_string
import requests
import time
from datetime import datetime
from django.utils import timezone

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
import string

from wham.apis.twitter.twitter_bearer_auth import BearerAuth as TwitterBearerAuth
from wham.fields import WhamDateTimeField, WhamForeignKey

FROM_LAST_ID = 'FROM_LAST_ID'

def dpath(d, path):
    node = d
    for property_name in path:
        node = node[property_name]
    return node

class WhamImproperlyConfigured(Exception):
    pass

class AlreadyCachedException(Exception):
    pass

wham_meta_required = [
    'endpoint'
]

wham_meta_attributes = {
    'required': ('endpoint',),
    'defaults': {
        'url_postfix': '',
        'auth_for_public_get': None,
        'requires_oauth_token': False,
        'url_pk_type': 'path',  #the primary key is assumed to be at the end of the path (not in the querysting) by default
        'url_pk_param': None,
        'api_key_param': 'api_key',
        'api_params': {},
        'params': {},
        'detail_base_result_path': (),
        'pager_type': None,
        'pager_param': None,
    }
}

wham_meta_search_attributes = {
    'required': (),
    'defaults': {
        'endpoint': '',
        'search_field': 'name',
        'results_path': (),
        'params': {},
        'search_param': 'q',
        'fields': None
    }
}

def check_n_set_class_attributes(klass, required, defaults, exclude=()):

    #check required attributes are set
    for key in required:
        if key not in vars(klass).keys():
            raise WhamImproperlyConfigured('WhamMeta must include the %s attribute' % key)

    #check for mistyped WhamMeta attributes
    for key in vars(klass).keys():
        if not key.startswith('__'):
            if (key not in defaults.keys() and
                    key not in exclude and
                    key not in required):
                raise WhamImproperlyConfigured('%s is not a valid WhamMeta attribute' % key)

    for key, value in deepcopy(defaults).iteritems():
        if not hasattr(klass, key):
            setattr(klass, key, value)

class WhamManager(models.Manager):

    use_for_related_fields = True

    http_cache = None

        # if we are a ManyRelatedManaer
        # if self.is_many_related_manager:
        #     self.init_wham_meta(model)
        # grrr this would have work, but there is this magic where
        # ManyRelatedManager becomes a subclass of *this* class rather than
        # the other way around and it does a super, but doesn't pass any friggen
        # arguments! see line 487 of django/db/models/fields/related.py
        # and this is the only place that model is passed through, and we
        # need model to get access to its Meta class.


    def init_wham_meta(self):
        model = self.model

        if not getattr(self, '_wham_meta', None):
            http_cache = getattr(settings, '_wham_http_cache', None)
            if not http_cache:
                settings._wham_http_cache = {}

            if hasattr(model, 'WhamMeta'):

                #check for required WhamMeta attributes
                self._wham_meta = getattr(model, 'WhamMeta', None)
                if not self._wham_meta:
                    raise WhamImproperlyConfigured("class inheriting from WhamModel requires a WhamMeta inner class")
                check_n_set_class_attributes(self._wham_meta,
                                             wham_meta_attributes['required'],
                                             wham_meta_attributes['defaults'],
                                             exclude=['Search'])
                self._wham_search_meta = getattr(self._wham_meta, 'Search', None)
                if self._wham_search_meta:
                    check_n_set_class_attributes(self._wham_search_meta,
                                                 wham_meta_search_attributes['required'],
                                                 wham_meta_search_attributes['defaults'])


    @property
    def is_many_related_manager(self):
        ducktype_attributes = ('_add_items', '_clear_items', '_remove_items')
        for attr in ducktype_attributes:
            if not hasattr(self, attr):
                return False
        return True

    def get_api_key(self):
        return getattr(settings, self.wham_meta.api_key_settings_name)

    def add_auth_params(self, params):
        if self._wham_meta.auth_for_public_get == 'API_KEY':
            params[self.api_key_param] = self.get_api_key()
        if self._wham_meta.requires_oauth_token:
            params['token'] = self.get_oauth_token()





    def make_get_request(self, url_tail, params=None, fetch_live=False, depth=1):

        session = requests.Session()
        if self._wham_meta.auth_for_public_get == 'TWITTER':
            twitter_auth = getattr(settings, 'twitter_auth', None)
            if not twitter_auth:
                settings.twitter_auth = TwitterBearerAuth(settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET)
                twitter_auth = settings.twitter_auth

            session.auth = twitter_auth

        url = self._wham_meta.base_url + url_tail + self._wham_meta.url_postfix

        final_params = self._wham_meta.params
        final_params.update(params if params else {})
        self.add_auth_params(final_params)
        if final_params:
            full_url = "%s?%s" % (url, urlencode(final_params))
        else:
            full_url = url
        print full_url

        if not fetch_live:
            if (full_url, depth) in settings._wham_http_cache:
                return settings._wham_http_cache[(full_url, depth)], True, full_url, depth
        else:
            pass
        response = session.get(url, params=final_params)
        response.raise_for_status()
        response_data = response.json()

        #this should have the request time or use the standard Django cache
        # this is a very basic cache that only caches results as long as the process is running, just
        # for demo purposes.
        return response_data, False, full_url, depth

    def get_fields(self):
        return [field for (field, _) in self.model._meta.get_fields_with_model()]

    def get_field_names(self):
        return [field.name for field in self.get_fields()]

    def get_field(self, field_name):
        return self.model._meta.get_field_by_name(field_name)[0]

    def dict_to_model_instance(self, dict):
        pass


    def get_from_dict(self, data, pk_dict_key='id'):

        field_names = self.get_field_names()

        kwargs = {}

        for field_name in field_names:
            field = self.get_field(field_name)
            result_path = field.get_result_path()
            try:
                value = dpath(data, result_path)
            except KeyError:
                pass
            else:
                if isinstance(field, WhamForeignKey):
                    fk_model_class = field.rel.to
                    if value is not None:
                        fk_instance = fk_model_class.objects.get_from_dict(value)
                    else:
                        fk_instance = None
                    kwargs[field_name] = fk_instance

                else:
                    if isinstance(field, WhamDateTimeField):
                        value = datetime.fromtimestamp(
                            time.mktime(time.strptime(value, '%a %b %d %H:%M:%S +0000 %Y')))
                        value = timezone.make_aware(value, timezone.get_default_timezone())

                    kwargs[field_name] = value

        try:
            instance = self.model.objects.get(pk=kwargs[pk_dict_key], wham_use_cache=True)
            for attr, value in kwargs.iteritems():
                setattr(instance, attr, value)
                instance.save()
        except ObjectDoesNotExist:
            instance = self.model.objects.create(**kwargs)

        #now we do m2m fields
        for field, _ in self.model._meta.get_m2m_with_model():
            related_class = field.rel.to
            wham_result_path = field.wham_result_path
            if not field.wham_result_path:
                wham_result_path = (field.name,)
            try:
                related_items = dpath(data, wham_result_path)
                for item in related_items:
                    related_class.objects.get_from_dict(item)
            except KeyError:
                pass

        return instance


    def get_wham_lookup_fields(self):
        fields = []
        for field in self.get_fields():
            if getattr(field, 'wham_can_lookup', False):
                fields.append(field)
        return fields

    def get_from_web(self, *args, **kwargs):

        fetch_live = kwargs.pop('fetch_live', False)

        pk_field_name = self.model._meta.pk.name

        if pk_field_name in kwargs or 'pk' in kwargs or 'id' in kwargs:
            if 'pk' in kwargs:
                pk = kwargs['pk']
            if 'id' in kwargs:
                pk = kwargs['id']
            elif pk_field_name in kwargs:
                pk = kwargs[pk_field_name]

            params = {}
            if self._wham_meta.url_pk_type == 'path':
                url_tail = self._wham_meta.endpoint + '/' + str(pk)
            elif self._wham_meta.url_pk_type == 'querystring':
                params[self._wham_meta.url_pk_param] = str(pk)
                url_tail = self._wham_meta.endpoint
            response_data, cached, full_url, depth = self.make_get_request(url_tail, params=params, fetch_live=fetch_live)
            if cached:
                raise AlreadyCachedException()
            else:
                settings._wham_http_cache[(full_url, depth)] = None

            item_data = dpath(response_data, self._wham_meta.detail_base_result_path)
            return self.get_from_dict(item_data, pk_dict_key=pk_field_name)
            # else:
            #     raise e  #TODO: make it obvious in the error message that the API returned a 404

        else:
            lookupable_fields = self.get_wham_lookup_fields()
            lookupable_fields_dict = {}
            for field in lookupable_fields:
                lookupable_fields_dict[field.name]= field.get_url_param()
            kwarg_field_names = {}
            for key in kwargs:
                query = key
                field_name = key.replace('__iexact', '')
                kwarg_field_names[field_name] = query
            field_names_to_lookup = set(lookupable_fields_dict.keys()) & set(kwarg_field_names)
            if len(field_names_to_lookup) == 0:
                raise Exception('query not supported by Rest API. TODO:fallback to regular django query')
            elif len(field_names_to_lookup) == 1:
                field_name = list(field_names_to_lookup)[0]
                url_param = lookupable_fields_dict[field_name]
                params = {url_param: kwargs[kwarg_field_names[field_name]]}
                response_data, cached, full_url, depth = \
                    self.make_get_request(self._wham_meta.endpoint, params=params, fetch_live=fetch_live)
                if cached:
                    raise AlreadyCachedException()
                else:
                    settings._wham_http_cache[(full_url, depth)] = None

                return self.get_from_dict(response_data)
            else:
                raise Exception('can only lookup one field at a time at this point')


    def get(self, *args, **kwargs):

        self.init_wham_meta()

        # this is a really dodgy hack
        # it's here because getting a twitter user by screen_name is case insensitive in twitter,
        # but a regular django get() is case sensitive. The hack is converting all
        # kwarg=value to kwarg__iexact=value


        for key, value in kwargs.iteritems():
            if key not in ['pk', 'id', 'wham_fetch_live', 'wham_use_cache', 'wham_depth']:
                kwargs[key + '__iexact'] = kwargs.pop(key)

        fetch_live = kwargs.pop('wham_fetch_live', False)
        use_cache = kwargs.pop('wham_use_cache', False)
        if use_cache:
            return super(WhamManager, self).get(*args, **kwargs)
        else:
            # TODO: we need to check that we can actually lookup the field in the api, if not do a regular django get()
            try:
                kwargs['fetch_live'] = fetch_live
                return self.get_from_web(*args, **kwargs) #always get from web for now
            except AlreadyCachedException:
                # then get cached result
                kwargs.pop('fetch_live')
                return super(WhamManager, self).get(*args, **kwargs)


    def filter(self, *args, **kwargs):
        self.init_wham_meta()

        search_meta = self._wham_search_meta
        if search_meta:
            search_field = search_meta.search_field #what??
            search_query = '%s__icontains' % search_field
            if search_query in kwargs:
                value = kwargs[search_query]

                url_tail = search_meta.endpoint
                params = search_meta.params
                search_param = search_meta.search_param
                params[search_param] = value

                response_data, cached, full_url, depth = \
                    self.make_get_request(url_tail, params=params)
                if cached:
                    return super(WhamManager, self).filter(*args, **kwargs)
                else:
                    settings._wham_http_cache[(full_url, depth)] = None
                    items = dpath(response_data, search_meta.results_path)
                    for item in items:
                        self.get_from_dict(item)

                    return super(WhamManager, self).filter(*args, **kwargs)

        return super(WhamManager, self).filter(*args, **kwargs)

    def all(self, *args, **kwargs):

        self.init_wham_meta()

        fetch_live = kwargs.pop('wham_fetch_live', False)
        use_cache = kwargs.pop('wham_use_cache', False)
        depth = kwargs.pop('wham_depth', 1)

        pages_to_get = kwargs.pop('wham_pages', 1)
        if pages_to_get == 'all':
            pages_to_get = 10000000
        pages_left = pages_to_get
        curr_page = 1
        last_id = None
        second_last_id = None

        def process_page(last_id, curr_page, pages_left):
            if pages_to_get > 1:
                if self._wham_meta.pager_type is not None:
                    if self._wham_meta.pager_type == FROM_LAST_ID:
                        if last_id is not None:
                            params[self._wham_meta.pager_param] = last_id
                    else:
                        raise Exception('paging is not implemented yet')
                else:
                    raise Exception('paging is not supported by this endpoint')


            response_data, cached, full_url, _ = self.make_get_request(
                endpoint, params, fetch_live=fetch_live, depth=depth)
            if cached:
                return response_data['last_id'] #in this case all we need to know from the cached data is the last_id... yeah I know...it's really confusing!

            pk_field_name = self.model._meta.pk.name
            items = dpath(response_data, m2m_field.wham_results_path)


            for item in items:
                item_id = item['id']  #we can't just assume the key is 'id'! but we will anyway #FIXME
                last_id = item_id

                if depth == 1:
                    item_instance = self.get_from_dict(item, pk_dict_key=pk_field_name)
                elif depth == 2:
                    item_instance = self.get(pk=item_id) #get the full object detail (requires a web request)

                if not self.filter(pk=item_instance.pk).exists():
                    if hasattr(self, 'add'):
                        self.add(item_instance)
                    else:
                        # a custom "through" model must have been specified
                        through_instance_create_kwargs = {}
                        for field in self.through._meta.fields:
                            if field.primary_key is True:
                                continue #no need to include the fk as we *assume* it's an autoincrementing id (naughty naughty) #FIXME
                            if isinstance(field, ForeignKey):
                                if issubclass(field.rel.to, m2m_field.related.model):
                                    through_instance_create_kwargs[field.name] = self.instance
                                    continue
                                if issubclass(field.rel.to, m2m_field.related.parent_model):
                                    through_instance_create_kwargs[field.name] = item_instance
                                    continue
                            # if it's not the primary key field, parent field or child field
                            through_instance_create_kwargs[field.name] = item[field.name]
                        self.through.objects.create(**through_instance_create_kwargs)


                else:
                    pass
                    #TODO we should really update the 'through' table fields if it exists

            #now that we know the last_id, we can finally store the cache data
            settings._wham_http_cache[(full_url, depth)] = {'last_id': last_id}
            return last_id

        if not use_cache:
            if self.is_many_related_manager:
                #get the source field
                source_class = self.source_field.rel.to
                m2m_field_name = self.prefetch_cache_name #this is a total hack. it *happens* to be the same as the m2m fieldname.
                m2m_field = getattr(source_class, m2m_field_name).field
                endpoint = Template(m2m_field.wham_endpoint).render(Context({'id': self.instance.pk}))
                params = m2m_field.wham_params
                if m2m_field.wham_pk_param:
                    params[m2m_field.wham_pk_param] = self.instance.pk

                while (pages_left >= 1):
                    second_last_id = last_id
                    last_id = process_page(last_id, curr_page, pages_left)
                    if second_last_id == last_id:
                        break
                    curr_page += 1
                    pages_left -= 1

        return super(WhamManager, self).all(*args, **kwargs)


    @property
    def docs(self):
        s = ''
        s += '\n  ' + string.ljust('Field', 30) + string.ljust('Type', 10)
        s += '\n----------------------------------------------------------------'
        for field in self.get_fields():
            prefix = '⚷ ' if field.primary_key else '  '
            s += '\n' + prefix + string.ljust(field.name, 30) + string.ljust(field.type_repr, 10)
        return s

    def _repr_html_(self):
        return render_to_string('wham/docs/endpoint.html', {'endpoint': self})

    def set_oauth_token(self, token):
        self.model.wham_oauth_token = token #store the token in the model class. why not.

    def get_oauth_token(self):
        return self.model.wham_oauth_token


class WhamModel(models.Model):

    objects = WhamManager()

    class Meta():
        abstract = True
