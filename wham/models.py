# -*- coding: utf-8 -*-
from copy import deepcopy
from urllib import urlencode, quote_plus

from django.conf import settings
from django.db.models import ForeignKey
from django.template import Template, Context
from django.template.loader import render_to_string
import requests
import time
from datetime import datetime, date
from django.utils import timezone


from django.core.exceptions import ObjectDoesNotExist
from django.db import models
import string

from .apis.twitter.twitter_bearer_auth import BearerAuth as TwitterBearerAuth
from .fields import WhamDateTimeField, WhamForeignKey

FROM_LAST_ID = 'FROM_LAST_ID'
NEXT_PAGE_URL = 'NEXT_PAGE_URL'

def dpath(d, path):
    node = d
    for property_name in path:
        node = node[property_name]
    return node


def urlencode_utf8(params):
    if hasattr(params, 'items'):
        params = params.items()
    return '&'.join(
        (quote_plus(k.encode('utf8'), safe='/') + '=' + quote_plus(unicode(v).encode('utf8'), safe='/')
            for k, v in params))

class WhamImproperlyConfigured(Exception):
    pass

class AlreadyCachedException(Exception):
    pass

wham_meta_attributes = {
    # 'required': ('endpoint',),
    'required': (),
    'defaults': {
        'endpoint': '',
        'url_postfix': '',
        'auth_for_public_get': None,
        'requires_oauth_token': False,
        'url_pk_type': 'path',  #the primary key is assumed to be at the end of the path (not in the querysting) by default
        'url_pk_param': None,
        'api_key_param': 'api_key',
        'token_param': 'token',
        'api_params': {},
        'params': {},
        'detail_base_result_path': (),
        'pager_type': None,
        'pager_param': None,
        'max_requests_per_day': None,
        'max_requests_per_minute': None,
        'not_found_error_path': None,
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

def remove_tzinfo(t):
    return t.replace(tzinfo=None)

def time_floor_to_minute(t):
    return t.replace(second=0, microsecond=0)

def get_this_minute():
    return time_floor_to_minute(timezone.now())

class RateLimitingDataManager(models.Manager):

    def get_for_app(self, app_label):
        return self.get(pk=app_label)

    def request_made(self, wham_model_class):
        app_label = wham_model_class._meta.app_label
        return self.get_for_app(app_label).request_made()

    def check_request_limit(self, wham_model_class):
        app_data = self.initialise(wham_model_class)
        return app_data.check_request_limit()

    def is_request_permitted(self, app_label):
        return self.get_for_app(app_label).is_request_permitted()

    # def

    def initialise(self, wham_model_class):
        """
        @param wham_model_class:  this can be any class for the API, you only need to provide one
        @return:
        """
        app_label = wham_model_class._meta.app_label
        data = {
            'max_requests_per_day': getattr(wham_model_class.WhamMeta, 'max_requests_per_day', None),
            'max_requests_per_minute': getattr(wham_model_class.WhamMeta, 'max_requests_per_minute', None),
            'minute_start': get_this_minute(),
        }
        try:
            row = self.get(pk=app_label)

        except ObjectDoesNotExist:
            row = self.create(
                pk=app_label,
                **data
            )
        return row


    def reset(self, wham_model_class):
        app_label = wham_model_class._meta.app_label
        data = {
            'max_requests_per_day': getattr(wham_model_class.WhamMeta, 'max_requests_per_day', None),
            'max_requests_per_minute': getattr(wham_model_class.WhamMeta, 'max_requests_per_minute', None),
            'minute_start': get_this_minute(),
            'requests_this_day': 0,
            'requests_this_minute': 0,
        }
        try:
            row = self.get(pk=app_label)
            for key, val in data.iteritems():
                setattr(row, key, data[key])
            row.save()

        except ObjectDoesNotExist:
            row = self.create(
                pk=app_label,
                **data
            )
        return row

class ReachedRequestLimit(Exception):
    pass

class ReachedDailyRequestLimit(ReachedRequestLimit):
    pass

class ReachedMaxRequestsPerMinuteLimit(ReachedRequestLimit):
    pass

class RateLimitingData(models.Model):
    objects = RateLimitingDataManager()

    app_label = models.CharField(max_length=100, primary_key=True)
    max_requests_per_day = models.IntegerField(null=True)
    max_requests_per_minute = models.IntegerField(null=True)
    day_start = models.DateField(auto_now_add=True)
    minute_start = models.DateTimeField()
    requests_this_day = models.IntegerField(default=0)
    requests_this_minute = models.IntegerField(default=0)
    max_total_requests_in_day = models.IntegerField(default=0)
    max_total_requests_in_minute = models.IntegerField(default=0)

    def check_request_limit(self):
        if not self.in_daily_limit():
            raise ReachedDailyRequestLimit(
                '%s requests made this day. %s daily limit'
                % (self.requests_this_day, self.max_requests_per_day)
            )
        if not self.in_minute_limit():
            raise ReachedMaxRequestsPerMinuteLimit(
                '%s requests made this minute. %s requests per minute permitted'
                % (self.requests_this_minute, self.max_requests_per_minute)
            )

    def request_made(self):
        #print 'request made'
        if self.has_day_ticked_over():
            self.max_total_requests_in_day = max(
                self.requests_this_day, self.max_total_requests_in_day)
            self.requests_this_day = 1
            self.day_start = timezone.now()
        elif self.has_minute_ticked_over():
            self.max_total_requests_in_minute = max(
                self.requests_this_minute, self.max_total_requests_in_minute)
            self.requests_this_minute = 1
            self.requests_this_day += 1
            self.requests_this_minute = 1
            self.minute_start = get_this_minute()
        else:
            self.requests_this_day += 1
            self.requests_this_minute += 1
        self.save()

    def in_daily_limit(self):
        if self.max_requests_per_day:
            if not (self.has_day_ticked_over()
                or self.requests_this_day < self.max_requests_per_day
                ):
                return False
        return True

    def in_minute_limit(self):
        if self.max_requests_per_minute:
            if not (self.has_minute_ticked_over()
                or self.requests_this_minute < self.max_requests_per_minute
                ):
                return False
        return True

    def has_day_ticked_over(self):
        if date.today() > self.day_start:
            self.max_total_requests_in_day = max(
                self.requests_this_day, self.max_total_requests_in_day)
            self.requests_this_day = 1
            self.day_start = timezone.now()
            self.save()
            return True
        else:
            return False

    def has_minute_ticked_over(self):
        this_minute = get_this_minute()
        minute_start = self.minute_start
        if this_minute > minute_start:
            self.max_total_requests_in_minute = max(
                self.requests_this_minute, self.max_total_requests_in_minute)
            self.requests_this_minute = 1
            self.minute_start = get_this_minute()
            self.save()
            return True
        else:
            return False

    def print_stats(self):
        print 'max_requests_per_day:', self.max_requests_per_day
        print 'max_requests_per_minute:', self.max_requests_per_minute
        print 'requests_this_day:', self.requests_this_day
        print 'requests_this_minute:', self.requests_this_minute
        print 'max_total_requests_in_day:', self.max_total_requests_in_day
        print 'max_total_requests_in_minute:', self.max_total_requests_in_minute
class WhamManager(models.Manager):

    use_for_related_fields = True

        # if we are a ManyRelatedManaer
        # if self.is_many_related_manager:
        #     self.init_wham_meta(model)
        # grrr this would have work, but there is this magic where
        # ManyRelatedManager becomes a subclass of *this* class rather than
        # the other way around and it does a super, but doesn't pass any friggen
        # arguments! see line 487 of django/db/models/fields/related.py
        # and this is the only place that model is passed through, and we
        # need model to get access to its Meta class.


    def init_wham_meta(self, **kwargs):
        model = self.model



        if not getattr(self, '_wham_meta', None):

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
        return getattr(settings, self._wham_meta.api_key_settings_name)

    def add_auth_params(self, params, oauth_token=None):
        if self._wham_meta.auth_for_public_get == 'API_KEY':
            params[self._wham_meta.api_key_param] = self.get_api_key()
        if self._wham_meta.requires_oauth_token:
            params[self._wham_meta.token_param] = oauth_token

    def get_request_url(self, url_tail, params=None, oauth_token=None):
        url = self._wham_meta.base_url + url_tail + self._wham_meta.url_postfix
        final_params = self._wham_meta.params
        final_params.update(params if params else {})
        self.add_auth_params(final_params, oauth_token=oauth_token)
        return url, final_params

    def make_get_request_with_full_url_path(self, url_path, params=None, depth=1):
        self.check_request_limit()
        session = requests.Session()
        if self._wham_meta.auth_for_public_get == 'TWITTER':
            twitter_auth = getattr(settings, 'twitter_auth', None)
            if not twitter_auth:
                settings.twitter_auth = TwitterBearerAuth(settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET)
                twitter_auth = settings.twitter_auth

            session.auth = twitter_auth

        # print 'url_path', url_path
        # print 'params', params
        response = session.get(url_path, params=params)


        response.raise_for_status()
        print 'response', response.content
        response_data = response.json()

        print 'params:', params
        if params:
            full_url = "%s?%s" % (url_path, urlencode_utf8(params))
        else:
            full_url = url_path
        print full_url

        self.request_made()
        return response_data, full_url, depth

    def make_get_request(self, url_tail, params=None, oauth_token=None, depth=1):
        if url_tail is None:
            url_tail = ''
        url, final_params = self.get_request_url(url_tail, params, oauth_token=oauth_token)
        return self.make_get_request_with_full_url_path(url, final_params)

    def check_request_limit(self):
        RateLimitingData.objects.check_request_limit(self.model)

    def request_made(self):
        RateLimitingData.objects.request_made(self.model)

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
                    # this assumes that the foreign key is where we're coming
                    # from. Sometimes we need to follow FK's to other places.
                    fk_model_class = field.rel.to
                    if value is not None:
                        if self.instance and type(self.instance) is field.rel.to:
                            fk_instance = self.instance
                        else:
                            if type(value) is dict:
                                fk_instance = fk_model_class.objects.get_from_dict(value)
                            else:
                                print 'doing a wham get... why?'
                                print 'we need some way of disabling this easily..with depth?'
                                fk_instance = None
                                #fk_instance = field.rel.to.objects.wham_get(pk=value)
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
            instance = self.model.objects.get(pk=kwargs[pk_dict_key])
            for attr, value in kwargs.iteritems():
                setattr(instance, attr, value)
            instance.save()
        except ObjectDoesNotExist:
            print 'kwargs: ', kwargs
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
                url_tail = self._wham_meta.endpoint + '/' + unicode(pk)
            elif self._wham_meta.url_pk_type == 'querystring':
                params[self._wham_meta.url_pk_param] = unicode(pk)
                url_tail = self._wham_meta.endpoint
            response_data, full_url, depth = self.make_get_request(url_tail, params=params)

            item_path_template = self._wham_meta.detail_base_result_path
            item_path = []
            for node_template in item_path_template:
                item_path.append(Template(node_template).render(Context({'pk': pk})))

            has_result = True
            if self._wham_meta.not_found_error_path:
                try:
                    dpath(response_data, self._wham_meta.not_found_error_path)
                    has_result = False
                except KeyError:
                    has_result = True

            if has_result:
                item_data = dpath(response_data, item_path)
                return self.get_from_dict(item_data, pk_dict_key=pk_field_name)
            else:
                raise ObjectDoesNotExist

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
                response_data, full_url, depth = \
                    self.make_get_request(self._wham_meta.endpoint, params=params)

                return self.get_from_dict(response_data)
            else:
                raise Exception('can only lookup one field at a time at this point')



    def wham_get(self, *args, **kwargs):
        kwargs['wham'] = True
        return self.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        wham = kwargs.pop('wham', False)
        if not wham:
            # do a regular django get()
            return super(WhamManager, self).get(*args, **kwargs)
        else:
            self.init_wham_meta(**kwargs)

            # this is a really dodgy hack
            # it's here because getting a twitter user by screen_name is case insensitive in twitter,
            # but a regular django get() is case sensitive. The hack is converting all
            # kwarg=value to kwarg__iexact=value


            for key, value in kwargs.iteritems():
                if key not in ['pk', 'id', 'wham_use_cache', 'wham_depth']:
                    kwargs[key + '__iexact'] = kwargs.pop(key)
            return self.get_from_web(*args, **kwargs)


    def wham_raw_api_filter(self, *args, **kwargs):
        kwargs['raw_api'] = True
        kwargs['wham'] = True
        return self.filter(self, *args, **kwargs)

    def wham_filter(self, *args, **kwargs):
        kwargs['wham'] = True
        return self.filter(*args, **kwargs)

    def filter(self, *args, **kwargs):

        wham = kwargs.pop('wham', False)
        raw_api = kwargs.pop('raw_api', False)
        if not wham:
            #do a regular filter()
            return super(WhamManager, self).filter(*args, **kwargs)

        self.init_wham_meta(**kwargs)

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

                response_data, full_url, depth = self.make_get_request(
                        url_tail, params=params)
                items = dpath(response_data, search_meta.results_path)

                if raw_api:
                    return response_data

                pk_field_name = self.model._meta.pk.name
                for item in items:
                    self.get_from_dict(item, pk_dict_key=pk_field_name)

        # do a regular filter()
        return super(WhamManager, self).filter(*args, **kwargs)


    def wham_all(self, *args, **kwargs):
        kwargs['wham'] = True
        return self.all(*args, **kwargs)

    def all(self, *args, **kwargs):
        wham = kwargs.pop('wham', False)
        if not wham:
            #do a regular django all()
            kwargs.pop('oauth_token', None)
            return super(WhamManager, self).all(*args, **kwargs)

        # helper functions for the all() method
        ####################################

        def process_fk_page_response_data(response_data, fk_field):
            pk_field_name = self.model._meta.pk.name
            items = dpath(response_data, fk_field.wham_results_path)

            last_id = None
            for item in items:
                item_id = item[pk_field_name]  #we can't just assume the key is 'id'! but we will anyway #FIXME
                last_id = item_id

                if depth == 1:
                    print 'getting from dict'
                    item_instance = self.get_from_dict(item, pk_dict_key=pk_field_name)
                elif depth == 2:
                    print 'getting full object detail'
                    item_instance = self.wham_get(pk=item_id) #get the full object detail (requires a web request)

                else:
                    pass
                    #TODO we should really update the 'through' table fields if it exists

            #now that we know the last_id, we can finally store the cache data
            return last_id

        def process_page_response_data(response_data):
            pk_field_name = self.model._meta.pk.name
            items = dpath(response_data, m2m_field.wham_results_path)

            last_id = None
            for item in items:
                item_id = item['id']  #we can't just assume the key is 'id'! but we will anyway #FIXME
                last_id = item_id

                if depth == 1:
                    item_instance = self.get_from_dict(item, pk_dict_key=pk_field_name)
                elif depth == 2:
                    item_instance = self.wham_get(pk=item_id) #get the full object detail (requires a web request)

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
            return last_id

        def get_next_page_url(page_response_data, last_id):
            if self._wham_meta.pager_type is not None:
                if self._wham_meta.pager_type == FROM_LAST_ID:
                    if last_id is not None:
                        params[self._wham_meta.pager_param] = last_id
                    next_page_url, final_params = self.get_request_url(endpoint, params)
                elif self._wham_meta.pager_type == NEXT_PAGE_URL:
                    final_params = None
                    try:
                        next_page_url = dpath(page_response_data, self._wham_meta.next_page_path)
                    except KeyError:
                        next_page_url = None
                else:
                    raise Exception('paging is not implemented yet')

                return next_page_url, final_params
            else:
                raise Exception('paging is not supported by this endpoint')


        # the main code for the all() method
        ####################################

        self.init_wham_meta(**kwargs)
        oauth_token = kwargs.pop('oauth_token', None)

        use_cache = kwargs.pop('wham_use_cache', False)
        depth = kwargs.pop('wham_depth', 1)

        pages_to_get = kwargs.pop('wham_pages', 1)
        if pages_to_get == 'all':
            pages_to_get = 10000000
        pages_left = pages_to_get
        curr_page = 1
        last_id = None
        second_last_id = None
        if not use_cache:
            if type(self).__name__ == 'RelatedManager': #for foreign keys

                print 'is fk'
                foreign_instance = self.instance
                fk_field = None
                for field in self.get_fields():
                    if (isinstance(field, ForeignKey) \
                            and type(self.model) == type(field.rel.to)
                        ):
                        fk_field = field
                        break
                templated_params = {}
                for key, value in fk_field.wham_params.iteritems():
                    templated_params[key] = Template(value).render(Context({'pk': self.instance.pk}))

                page_response_data, full_url, __ = self.make_get_request(
                    fk_field.wham_endpoint, templated_params, depth=depth)
                process_fk_page_response_data(page_response_data, fk_field)
                pass

                # fk_field.wham_endpoint
                # fk_field.wham_params
                # fk_field.wham_pk_param
                # fk_field.wham_result_path



            elif self.is_many_related_manager:

                # we must handle the case where this is a ForeignKey... not a M2M... didn't we already
                # do that somewhere?? somewhere new? or did we always hack it for twitter? Spotify maybe?

                #get the source field
                source_class = self.source_field.rel.to
                m2m_field_name = self.prefetch_cache_name #this is a total hack. it *happens* to be the same as the m2m fieldname.
                m2m_field = getattr(source_class, m2m_field_name).field
                endpoint = Template(m2m_field.wham_endpoint).render(Context({'pk': self.instance.pk}))
                params = m2m_field.wham_params
                if m2m_field.wham_pk_param:
                    params[m2m_field.wham_pk_param] = self.instance.pk

                page_response_data, full_url, __ = self.make_get_request(
                    endpoint, params, depth=depth, oauth_token=oauth_token)
                last_id = process_page_response_data(page_response_data)

                while pages_left >= 1:
                    url_path, params = get_next_page_url(page_response_data, last_id)
                    if url_path is None:
                        break
                    page_response_data, full_url, __ = self.make_get_request_with_full_url_path(url_path, params)
                    second_last_id = last_id
                    last_id = process_page_response_data(page_response_data)
                    if second_last_id == last_id:
                        break
                    curr_page += 1
                    pages_left -= 1
            else:
                # we don't bother handling this case yet. It's pretty rare that
                # a public API will provide a list of all objects for a endpoint (there's
                # usually thousands of them)
                pass

        #finish by doing a regular django all()
        kwargs.pop('oauth_token', None)
        kwargs.pop('wham', False)
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


class WhamModel(models.Model):

    objects = WhamManager()

    class Meta():
        abstract = True


