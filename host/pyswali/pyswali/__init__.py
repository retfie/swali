"""Implement an API wrapper around SWALI VSCP."""

from .error import (
    PyswaliError, RequestError, RequestTimeout)
from .gateway import gateway

__all__ = ['gateway', 'light', 'PyswaliError', 'RequestError', 'RequestTimeout']
