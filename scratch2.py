import inspect


class B(object):
    att1 = 'att1'
    att2 = 'att2'


class A(object):

    def __init__(self):
        # print B.__dict__
        print inspect.getmembers(B)
        # setattr(object, name, pass)


a = A()
