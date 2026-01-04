# click_app/__init__.py
__version__ = '1.2.0'

__all__ = []

from .click_gui import *
__all__ += getattr(__import__(__name__ + '.click_gui', fromlist=['__all__']), '__all__', [])

