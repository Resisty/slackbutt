#!/usr/bin/env python
""" Module for impersonating numbers in various ways
"""

# pylint: disable=too-few-public-methods

class NoNumberError(Exception):
    """ Custom error class
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class NumberString:
    """ Represent number as a string
    """
    @classmethod
    def from_str(cls, numstring):
        """ Create an instance based on a string number
        """
        for i in [IntString, BinString, HexString, FloatString]:
            try:
                _ = i(numstring).num
                return i(numstring)
            except ValueError:
                continue
        raise NoNumberError()

class IntString:
    """ Class for representing string number as an integer
    """
    def __init__(self, s):
        self._str = s
        self._num = None
        self._base = 10
        self._tonum = int
        self._tostr = str

    def __add__(self, other):
        return self.__class__(str(self.num + other))

    def __sub__(self, other):
        return self.__class__(str(self.num - other))

    def __iadd__(self, other):
        self.num += other
        return self

    def __isub__(self, other):
        self.num -= other
        return self

    def __repr__(self):
        return self._tostr(self.num)

    def __str__(self):
        return self._tostr(self.num)

    @property
    def num(self):
        """ Propertize ourself as a number
        """
        if not self._num:
            self._num = self._tonum(self._str, self._base)
        return self._num

    @num.setter
    def num(self, newnumber):
        self._num = newnumber
        return self.num

    @property
    def str(self):
        """ No reason not to implement this, I guess
        """
        return self._tostr(self.num)

class BinString(IntString):
    """ Class for representing string number as a binary integer
    """
    def __init__(self, s):
        super(BinString, self).__init__(s)
        try:
            assert s.startswith('0b')
        except AssertionError:
            raise ValueError()
        self._base = 2
        self._tostr = bin

class HexString(IntString):
    """ Class for representing string number as a hexadecimal integer
    """
    def __init__(self, s):
        super(HexString, self).__init__(s)
        try:
            assert s.startswith('0x')
        except AssertionError:
            raise ValueError()
        self._base = 16
        self._tostr = hex

class FloatString(IntString):
    """ Class for representing string number as a float
    """
    def __init__(self, s):
        super(FloatString, self).__init__(s)
        self._tonum = float

    @property
    def num(self):
        if not self._num:
            self._num = self._tonum(self._str)
        return self._num

    @num.setter
    def num(self, x):
        self._num = x
        return self.num
