from ..utils.pagination import CustomPageNumberPagination


class PaginationMixin:
    """
    Mixin to provide custom pagination for viewsets
    """
    pagination_class = CustomPageNumberPagination
