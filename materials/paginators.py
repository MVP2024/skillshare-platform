from rest_framework.pagination import PageNumberPagination


class MaterialsPagination(PageNumberPagination):
    """
    Пагинация для курсов и уроков.

    - page_size: Количество элементов на странице (10)
    - page_size_query_param: Параметр для изменения размера страницы
    - max_page_size: Максимальное количество элементов на странице (100)
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
