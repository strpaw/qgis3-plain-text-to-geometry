"""Custom exceptions for the PlainTextToGeometry plugin."""

class PlainTextToGeometryException(Exception):
    """Base exception for the PlainTextToGeometry plugin."""


class FormValidationException(PlainTextToGeometryException):
    """Raised when form input is invalid."""
