from typing import Mapping


def build_set_clause(
    update_fields: dict,
    column_map: Mapping[str, str]
) -> tuple[str, dict]:
    """
    안전한 UPDATE SET 절 생성.

    Args:
        update_fields: 업데이트할 필드와 값 {"title": "new title", ...}
        column_map: 허용된 필드 -> DB 컬럼 매핑 {"title": "title", "content": "content"}

    Returns:
        (set_clause, params) 튜플
        - set_clause: "title = %(title)s, content = %(content)s"
        - params: {"title": "new title", "content": "..."}

    Example:
        >>> column_map = {"title": "title", "content": "content"}
        >>> update_fields = {"title": "Hello", "role": "admin"}  # role은 무시됨
        >>> clause, params = build_set_clause(update_fields, column_map)
        >>> clause
        'title = %(title)s'
        >>> params
        {'title': 'Hello'}
    """
    set_parts = []
    params = {}

    for field_name, value in update_fields.items():
        if field_name in column_map:
            # 매핑된 컬럼명(하드코딩)을 사용 - SQL Injection 방지
            column_name = column_map[field_name]
            set_parts.append(f"{column_name} = %({field_name})s")
            params[field_name] = value

    return ", ".join(set_parts), params
