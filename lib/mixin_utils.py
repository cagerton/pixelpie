import logging


class MixedClassMeta(type):
    """Mixin to call constructors of mixins...

    https://stackoverflow.com/questions/6098970/are-mixin-class-init-functions-not-automatically-called-in-python
    """
    def __new__(cls, name, bases, classdict):
        classinit = classdict.get('__init__')  # could be None
        # define an __init__ function for the new class

        def __init__(self, *args, **kwargs):
            # call the __init__ functions of all the bases
            for base in type(self).__bases__:
                base.__init__(self, *args, **kwargs)
            # also call any __init__ function that was in the new class
            if classinit:
                classinit(self, *args, **kwargs)
        # add the local function to the new class
        classdict['__init__'] = __init__

        return type.__new__(cls, name, bases, classdict)


