from django.db import models

# the following will be required if we want to support south
# ----------------------------------------------------------------
# from south.modelsinspector import add_introspection_rules
#
# add_introspection_rules([], [
#     "^wham\.models\.WhamCharField",
#     "^wham\.models\.WhamTextField",
#     "^wham\.models\.WhamIntegerField",
#     "^wham\.models\.WhamFloatField",
#     "^wham\.models\.WhamManyToManyField",
#     "^wham\.models\.WhamDateField",
#     "^wham\.models\.WhamDateTimeField",
#     "^wham\.models\.WhamImageUrlField",
# ])



class WhamFieldMixin(object):
    def __init__(self, *args, **kwargs):
        self.wham_result_path = kwargs.pop('wham_result_path', None)
        self.wham_can_lookup = kwargs.pop('wham_can_lookup', False)
        self.wham_url_param = kwargs.pop('wham_url_param', None)
        self.wham_detailed = kwargs.pop('wham_detailed', False)
        return super(WhamFieldMixin, self).__init__(*args, **kwargs)

    def get_result_path(self):
        result_path = self.wham_result_path
        if not result_path:
            return (self.attname,)
        else:
            return result_path

    def get_url_param(self):
        return self.wham_url_param if self.wham_url_param else self.name


class WhamCharField(WhamFieldMixin, models.TextField):

    @property
    def type_repr(self):
        return 'char'

class WhamTextField(WhamFieldMixin, models.TextField):

    @property
    def type_repr(self):
        return 'text'

class WhamIntegerField(WhamFieldMixin, models.IntegerField):

    @property
    def type_repr(self):
        return 'integer'

class WhamFloatField(WhamFieldMixin, models.FloatField):

    @property
    def type_repr(self):
        return 'float'

class WhamDateField(WhamFieldMixin, models.DateField):
    pass

class WhamDateTimeField(WhamFieldMixin, models.DateTimeField):

    def __init__(self, *args, **kwargs):
        self.wham_format = kwargs.pop('wham_format', None)
        return super(WhamDateTimeField, self).__init__(*args, **kwargs)

class WhamManyToManyField(models.ManyToManyField):

    def __init__(self, *args, **kwargs):
        self.wham_result_path = kwargs.pop('wham_result_path', None)
        self.wham_endpoint = kwargs.pop('wham_endpoint', None)
        self.wham_results_path = kwargs.pop('wham_results_path', ())
        self.wham_pk_param = kwargs.pop('wham_pk_param', None)
        self.wham_params = kwargs.pop('wham_params', {})
        return super(WhamManyToManyField, self).__init__(*args, **kwargs)




    @property
    def type_repr(self):
        return 'many to many'


class WhamForeignKey(models.ForeignKey):

    def __init__(self, *args, **kwargs):
        self.wham_result_path = kwargs.pop('wham_result_path', None)
        self.wham_endpoint = kwargs.pop('wham_endpoint', None)
        self.wham_results_path = kwargs.pop('wham_results_path', ())
        self.wham_pk_param = kwargs.pop('wham_pk_param', None)
        self.wham_params = kwargs.pop('wham_params', {})
        return super(WhamForeignKey, self).__init__(*args, **kwargs)

    def get_result_path(self):
        result_path = self.wham_result_path
        if not result_path:
            return (self.name,)
        else:
            return result_path

    @property
    def type_repr(self):
        return 'foreign key'

class WhamImageUrlField(WhamTextField):
    pass

