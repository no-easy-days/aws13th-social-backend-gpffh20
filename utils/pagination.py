def paginate(items: list, page: int, page_size: int) -> tuple[list, int, int]:
    """
    리스트 페이지네이션 처리

    Args:
        items: 전체 아이템 리스트
        page: 요청 페이지 번호
        page_size: 페이지당 아이템 수

    Returns:
        (paginated_items, actual_page, total_pages)
    """
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    actual_page = min(page, total_pages)

    start = (actual_page - 1) * page_size
    end = start + page_size

    return items[start:end], actual_page, total_pages
