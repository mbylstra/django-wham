# class ClassA:
#     d = {}
#
# instance = ClassA()
# instance.d['x'] = 1
#
# instance2 = ClassA()
# print instance2.d

###########################
from copy import deepcopy

defaults = {
    'a': 'default',
    'b': {}
}

class ClassA:
    a = 'instance_a'

    def __init__(self):
        for key, value in deepcopy(defaults).iteritems():
            if not hasattr(self, key):
                setattr(self, key, value)

class ClassB:
    a = 'instance_a'
    z = 'z'

    def __init__(self):

        #check for mistyped WhamMeta attributes
        for key in vars(self.__class__).keys():
            if not key.startswith('__'):
                if key not in defaults.keys():
                    raise
        print vars(self.__class__)
        for key, value in deepcopy(defaults).iteritems():
            if not hasattr(self, key):
                setattr(self, key, value)


instance = ClassA()
instance.b['new'] = 'new'

instance2 = ClassB()


print instance.a
print instance.b
print instance2.b
