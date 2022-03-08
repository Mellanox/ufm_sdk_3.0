class SingletonException(Exception):
    pass

# Singleton implementation has been taken from http://www.garyrobinson.net/2004/03/python_singleto.html


class MetaSingleton(type):
    def __new__(metaclass, strName, tupBases, dict):
        if '__new__' in dict:
            raise SingletonException('Can not override __new__ in a Singleton')
        return super(MetaSingleton, metaclass).__new__(metaclass, strName, tupBases, dict)

    def __call__(cls, *lstArgs, **dictArgs):
        raise SingletonException('Singletons may only be instantiated through getInstance()')


class Singleton(object, metaclass=MetaSingleton):

    def getInstance(cls, *lstArgs):
        '''
        Call this to instantiate an instance or retrieve the existing instance.
        If the singleton requires args to be instantiated, include them the first
        time you call getInstance.
        '''
        if cls._isInstantiated():
            if len(lstArgs) != 0:
                raise SingletonException(
                    'If no supplied args, singleton must already be instantiated, or __init__ must require no args')
        else:
            if cls._getConstructionArgCountNotCountingSelf() > 0 and len(lstArgs) <= 0:
                raise SingletonException('If the singleton requires __init__ args, supply them on first instantiation')
            instance = cls.__new__(cls)
            instance.__init__(*lstArgs)
            cls.cInstance = instance
        return cls.cInstance

    getInstance = classmethod(getInstance)

    def _isInstantiated(cls):
        '''
        checks if the class has instance
        @returns true if the class has instance
        '''
        return hasattr(cls, 'cInstance') and isinstance(cls.cInstance, cls)

    _isInstantiated = classmethod(_isInstantiated)

    def _getConstructionArgCountNotCountingSelf(cls):
        '''
        calculates number of arguments passed when class was instantiated
        @return: number of arguments passed when class was instantiated
        '''
        return cls.__init__.__code__.co_argcount - 1

    _getConstructionArgCountNotCountingSelf = classmethod(_getConstructionArgCountNotCountingSelf)

    def _forgetClassInstanceReferenceForTesting(cls):
        """
        This is designed for convenience in testing -- sometimes you
        want to get rid of a singleton during test code to see what
        happens when you call getInstance() under a new situation.
        pyinotify
        To really delete the object, all external references to it
        also need to be deleted.
        """
        try:
            delattr(cls, 'cInstance')
        except AttributeError:
            # run up the chain of base classes until we find the one that has the instance
            # and then delete it there
            for baseClass in cls.__bases__:
                if issubclass(baseClass, Singleton):
                    baseClass._forgetClassInstanceReferenceForTesting()

    _forgetClassInstanceReferenceForTesting = classmethod(_forgetClassInstanceReferenceForTesting)
