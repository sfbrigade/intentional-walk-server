from typing import List, TypedDict
from enum import Enum


class FieldType(Enum):
    """Represents data types for Faker to generate."""

    EMAIL = "email"
    NAME = "name"


class PrivateFieldInfo(TypedDict):
    """Represents a sensitive field in a model."""

    name: str
    type: FieldType


class PrivacyProtectedFieldsMixin:
    """Mixin to define sensitive fields in a model.

    A downstream handler for a Model that extends this mixin should
    implement the `privacy_protected_fields` method to return the list of
    sensitive fields that should be scrubbed, hidden away or otherwise excluded.

    Example use:
    ```python
    class Account(models.Model, PrivacyProtectedFieldsMixin):
        email = models.EmailField()
        def privacy_protected_fields():
            return ["email", "name"]
    ```
    """

    @staticmethod
    def privacy_protected_fields() -> List[PrivateFieldInfo]:
        """Return a list of sensitive fields in the model."""
        raise NotImplementedError
