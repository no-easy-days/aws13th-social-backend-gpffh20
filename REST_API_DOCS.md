# 클라우드 커뮤니티 REST API Docs

## 내가 좋아요한 게시글 목록

**GET** `/posts/liked`

로그인한 사용자가 좋아요를 누른 게시글 목록을 페이지네이션을 적용하여 게시글 20개 씩 조회 합니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Query Parameters**

| 파라미터  | 타입      | 필수 | 설명                                    |
|-------|---------|----|---------------------------------------|
| page  | number  | X  | 조회할 페이지 번호입니다. (default=1)            |
| limit | number  | X  | 한 페이지에 포함될 게시글 수입니다. (default=20)     |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "post_301",
      "author": "user_777",
      "title": "좋아요한 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:00:00Z"
    },
    {
      "id": "post_302",
      "author": "user_123",
      "title": "두 번째 좋아요한 게시글",
      "view_count": 30,
      "like_count": 2,
      "created_at": "2026-01-05T09:10:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 37
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "liked",
      "reason": "invalid_type",
      "value": "abc"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

---

### 좋아요 상태 확인

**GET** `/posts/{post_id}/likes`

특정 게시글에 대해 현재 로그인한 사용자의 좋아요 여부와 총 좋아요 수를 조회합니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명                       |
|---------|--------|----|--------------------------|
| post_id | string | O  | 좋아요 상태 확인 할 게시글의 id 입니다. |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "liked": true,
    "like_count": 45
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "post_id",
      "reason": "invalid_format",
      "value": "post__"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 내가 쓴 댓글 목록

**GET** `/comments/me`

로그인한 사용자가 본인이 작성한 댓글 목록을 페이지네이션을 적용하여 20개 씩 조회합니다

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Query Parameters**

| 파라미터  | 타입      | 필수 | 설명                                  |
|-------|---------|----|-------------------------------------|
| page  | number  | X  | 조회할 페이지 번호입니다. (default=1)          |
| limit | number  | X  | 한 페이지에 포함될 게시글 수입니다. (default=20)   |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "comment_123",
      "post_id": "post_123",
      "author": "user_123",
      "content": "내가 쓴 댓글입니다.",
      "created_at": "2026-01-04T12:00:00Z"
    },
    {
      "id": "comment_124",
      "post_id": "post_321",
      "author": "user_123",
      "content": "다른 게시글에 쓴 댓글입니다.",
      "created_at": "2026-01-05T09:10:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 37
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "page",
      "reason": "invalid_type",
      "value": "abc"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

---

### 댓글 목록 조회

**GET** `/posts/{post_id}/comments`

특정 게시글에 작성된 댓글 목록을 페이지네이션을 적용하여 10개씩 조회합니다.

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명                  |
|---------|--------|----|---------------------|
| post_id | string | O  | 댓글 조회할 게시글의 id 입니다. |

**Query Parameters**

| 파라미터  | 타입     | 필수 | 설명                                |
|-------|--------|----|-----------------------------------|
| page  | number | X  | 조회할 페이지 번호입니다. (default=1)        |
| limit | number | X  | 한 페이지에 포함될 게시글 수입니다. (default=10) |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "comment_123",
      "post_id": "post_123",
      "author": "user_123",
      "content": "첫 번째 댓글입니다.",
      "created_at": "2026-01-04T12:00:00Z"
    },
    {
      "id": "comment_124",
      "post_id": "post_123",
      "author": "user_321",
      "content": "두 번째 댓글입니다.",
      "created_at": "2026-01-04T12:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 37
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "post_id",
      "reason": "invalid_format",
      "value": "post__"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 내가 쓴 게시글 목록

**GET** `/posts/me`

로그인한 사용자가 본인이 작성한 게시글 목록을 페이지네이션을 적용하여 게시물 20개씩 조회합니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Query Parameters**

| 파라미터  | 타입      | 필수 | 설명                                   |
|-------|---------|----|--------------------------------------|
| page  | number  | X  | 조회할 페이지 번호입니다. (default=1)           |
| limit | number  | X  | 한 페이지에 포함될 게시글 수입니다. (default=20)    |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "post_123",
      "author": "user_123",
      "title": "내가 쓴 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:00:00Z"
    },
    {
      "id": "post_124",
      "author": "user_123",
      "title": "내가 쓴 두 번째 게시글",
      "view_count": 30,
      "like_count": 2,
      "created_at": "2026-01-05T09:10:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 37
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "page",
      "reason": "invalid_type",
      "value": "abc"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

---

### 게시글 상세 조회

**GET** `/posts/{post_id}`

특정 게시글을 단건 조회합니다. 게시글 조회에 성공하면 해당 게시글의 조회수가 자동으로 1 증가합니다.

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명               |
|---------|--------|----|------------------|
| post_id | string | O  | 조회할 게시글의 id 입니다. |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "id": "post_123",
    "author": "user_123",
    "title": "첫 번째 게시글",
    "content": "게시글 내용입니다.",
    "view_count": 121,
    "like_count": 45,
    "created_at": "2026-01-04T12:00:00Z"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "post_id",
      "reason": "invalid_format",
      "value": "post__"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

**Response (429 Rate Limited)**

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMITED",
    "message": "요청이 너무 많습니다.",
    "details": {
      "retry_after_seconds": 30
    }
  }
}
```

---

### 게시글 정렬

**GET** `/posts`

게시글 목록을 조회하며, 정렬 기준(sort)과 정렬 방향(order)을 통해 최신순, 조회수순, 좋아요순 정렬이 가능합니다. 페이지네이션을 통해 20개의 게시물씩 반환합니다.

**Query Parameters**

| 파라미터  | 타입     | 필수 | 설명                                             |
|-------|--------|----|------------------------------------------------|
| sort  | string | X  | 정렬 기준입니다. (created_at, view_count, like_count) |
| order | string | X  | 정렬 방향입니다. (asc, desc)                          |
| page  | number | X  | 조회할 페이지 번호입니다. (default=1)                     |
| limit | number | X  | 한 페이지에 포함될 게시글 수입니다. (default=20)              |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "post_123",
      "author": "user_123",
      "title": "첫 번째 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:05:00Z"
    },
    {
      "id": "post_124",
      "author": "user_321",
      "title": "두 번째 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 145
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "sort",
      "reason": "invalid_value",
      "value": "random"
    }
  }
}
```

---

### 게시글 검색

**GET** `/posts`

검색 조건을 기준으로 게시글을 검색합니다. 검색어를 전달받아 제목이나 내용에 포함되는 게시글 목록을 20개씩 반환합니다.

**Query Parameters**

| 파라미터    | 타입     | 필수 | 설명                                               |
|---------|--------|----|--------------------------------------------------|
| keyword | string | X  | 게시글 제목 또는 내용에 포함된 검색어입니다. 검색어가 없으면 전체 목록을 반환합니다. |
| page    | number | X  | 조회할 페이지 번호입니다. (default=1)                       |
| limit   | number | X  | 한 페이지에 포함될 게시글 수입니다. (default=20)                |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "post_123",
      "author": "user_123",
      "title": "검색된 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 35
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "page",
      "reason": "invalid_type",
      "value": "abc"
    }
  }
}
```

---

### 게시글 목록 조회

**GET** `/posts`

모든 게시글 목록을 페이지네이션을 적용하여 조회합니다. 페이지 번호를 기준으로 게시글 20개 씩 페이지네이션 하여 게시글 목록을 반환합니다.

| 파라미터  | 타입     | 필수 | 설명                                  |
|-------|--------|----|-------------------------------------|
| page  | number | X  | 조회할 페이지 번호입니다. (default=1)          |
| limit | number | X  | 한 페이지에 포함 될 게시글 수 입니다. (default=20) |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": [
    {
      "id": "post_123",
      "author": "user_123",
      "title": "첫 번째 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:00:00Z"
    },
    {
      "id": "post_124",
      "author": "user_321",
      "title": "두 번째 게시글",
      "view_count": 120,
      "like_count": 45,
      "created_at": "2026-01-04T12:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 145
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "page",
      "reason": "invalid_type",
      "value": "abc"
    }
  }
}
```

---

### 특정 회원 조회

**GET** `/users/{user_id}`

특정 회원의 프로필을 조회합니다.

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명              |
|---------|--------|----|-----------------|
| user_id | string | O  | 조회할 회원의 id 입니다. |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "id": "user_321",
    "nickname": "user321",
    "profile_img": "/images/profiles/user321.png"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "user_id",
      "reason": "invalid_format",
      "value": "user__"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "user",
      "id_field": "user_id",
      "id": "user_999"
    }
  }
}
```

---

### 내 프로필 조회

**GET** `/users/me`

로그인 된 회원 본인의 프로필을 조회합니다. 요청한 회원과 조회 대상자가 동일한 경우, 해당 회원의 프로필 정보를 반환합니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "id": "user_123",
    "email": "example@gmail.com",
    "nickname": "user123",
    "profile_img": "/images/profiles/user123.png",
    "created_at": "2026-01-04T12:00:00Z"
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

---

### 좋아요 취소

**POST** `/posts/{post_id}/likes`

(**같은 엔드포인트 재사용**)로그인한 사용자가 특정 게시글에 좋아요를 취소합니다. 이미 좋아요를 취소한 게시글에 다시 요청할 경우 좋아요가 등록됩니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명                     |
|---------|--------|----|------------------------|
| post_id | string | O  | 좋아요를 취소 할 게시글의 id 입니다. |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "liked": false,
    "like_count": 46
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "post_id",
      "reason": "invalid_format",
      "value": "post__"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 좋아요 등록

**POST** `/posts/{post_id}/likes`

로그인한 사용자가 특정 게시글에 좋아요를 등록합니다. 이미 좋아요를 누른 게시글에 다시 요청할 경우 좋아요가 취소됩니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명                 |
|---------|--------|----|--------------------|
| post_id | string | O  | 좋아요 할 게시글의 id 입니다. |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "liked": true,
    "like_count": 46
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "post_id",
      "reason": "invalid_format",
      "value": "post__"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 댓글 삭제

**DELETE** `/posts/{post_id}/comments/{comment_id}`

로그인한 사용자가 본인이 작성한 댓글을 삭제합니다. 요청한 사용자가 댓글 작성자가 아닌 경우 삭제할 수 없습니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터       | 타입     | 필수 | 설명                  |
|------------|--------|----|---------------------|
| post_id    | string | O  | 삭제할 댓글의 게시글 id 입니다. |
| comment_id | string | O  | 삭제할 댓글의 id 입니다.     |

**Response (204 No Content)**

```json
204 No Content
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "comment_id",
      "reason": "invalid_format",
      "value": "comment__"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (403 Forbidden)**

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "요청한 작업을 수행할 권한이 없습니다.",
    "details": {
      "reason": "not_comment_owner",
      "resource": "comment",
      "id_field": "comment_id",
      "id": "comment_123"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "comment",
      "id_field": "comment_id",
      "id": "comment_999"
    }
  }
}
```

---

### 댓글 수정

**PATCH** `/posts/{post_id}/comments/{comment_id}`

로그인한 사용자가 본인이 작성한 댓글을 수정합니다. 요청한 사용자가 댓글 작성자가 아닌 경우 수정할 수 없습니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Content-Type  | string | O  | 요청 데이터를 application/json 형태로 전송합니다.                                       |
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터       | 타입     | 필수 | 설명                  |
|------------|--------|----|---------------------|
| post_id    | string | O  | 수정할 댓글의 게시글 id 입니다. |
| comment_id | string | O  | 수정할 댓글의 id 입니다.     |

**Request Body**

| 필드      | 타입     | 필수 | 설명                            |
|---------|--------|----|-------------------------------|
| content | string | O  | 수정할 댓글 내용입니다. 빈 값을 넣을 수 없습니다. |

**Request**

```json
{
  "content": "수정된 댓글입니다."
}
```

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "id": "comment_123",
    "post_id": "post_123",
    "author": "user_123",
    "content": "수정된 댓글입니다.",
    "created_at": "2026-01-04T12:00:00Z",
    "updated_at": "2026-01-08T06:30:00Z"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "content",
      "reason": "missing_or_empty",
      "value": ""
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (403 Forbidden)**

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "요청한 작업을 수행할 권한이 없습니다.",
    "details": {
      "reason": "not_comment_owner",
      "resource": "comment",
      "id_field": "comment_id",
      "id": "comment_123"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "comment",
      "id_field": "comment_id",
      "id": "comment_999"
    }
  }
}
```

---

### 댓글 작성

**POST** `/posts/{post_id}/comments`

로그인한 사용자가 특정 게시글에 댓글을 작성합니다. 요청 본문에 content를 포함해야 하며, 생성에 성공하면 댓글 ID와 생성 시간이 자동으로 할당됩니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Content-Type  | string | O  | 요청 데이터를 application/json 형태로 전송합니다.                                       |
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명                  |
|---------|--------|----|---------------------|
| post_id | string | O  | 댓글 작성할 게시글의 id 입니다. |

**Request Body**

| 필드      | 타입     | 필수 | 설명                        |
|---------|--------|----|---------------------------|
| content | string | O  | 댓글 내용입니다. 빈 값을 넣을 수 없습니다. |

**Request**

```json
{
  "content": "첫 번째 댓글입니다."
}
```

**Response (201 Created)**

```json
{
  "status": "success",
  "data": {
    "id": "comment_125",
    "post_id": "post_123",
    "author": "user_123",
    "content": "첫 번째 댓글입니다.",
    "created_at": "2026-01-08T06:10:00Z"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "content",
      "reason": "missing_or_empty",
      "value": ""
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 게시글 삭제

**DELETE** `/posts/{post_id}`

로그인한 사용자가 본인이 작성한 게시글을 삭제합니다. 요청한 사용자가 게시글 작성자가 아닌 경우 삭제할 수 없습니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명               |
|---------|--------|----|------------------|
| post_id | string | O  | 삭제할 게시글의 id 입니다. |

**Response (204 No Content)**

```json
204 No Content
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "post_id",
      "reason": "invalid_format",
      "value": "post__"
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (403 Forbidden)**

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "요청한 작업을 수행할 권한이 없습니다.",
    "details": {
      "reason": "not_post_owner",
      "resource": "post",
      "id_field": "post_id",
      "id": "post_123"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 게시글 수정

**PATCH** `/posts/{post_id}`

로그인한 회원은 본인이 작성한 게시글을 수정합니다. 요청한 회원이 게시글 작성자가 아닌 경우 수정할 수 없습니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Content-Type  | string | O  | 요청 데이터를 application/json 형태로 전송합니다.                                       |
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Path Parameters**

| 파라미터    | 타입     | 필수 | 설명               |
|---------|--------|----|------------------|
| post_id | string | O  | 수정할 게시글의 id 입니다. |

**Request Body**

| 필드      | 타입     | 필수 | 설명                                 |
|---------|--------|----|------------------------------------|
| title   | string | X  | 수정할 게시글 제목입니다. 포함하지 않으면 변경되지 않습니다. |
| content | string | X  | 수정할 게시글 내용입니다. 포함하지 않으면 변경되지 않습니다. |

**Request Example**

```json
{
  "title": "수정된 제목",
  "content": "수정된 내용입니다."
}
```

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "id": "post_123",
    "author": "user_123",
    "title": "수정된 제목",
    "content": "수정된 내용입니다.",
    "view_count": 121,
    "like_count": 45,
    "created_at": "2026-01-04T12:00:00Z",
    "updated_at": "2026-01-08T05:20:00Z"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "content",
      "reason": "missing_or_empty",
      "value": ""
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (403 Forbidden)**

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "요청한 작업을 수행할 권한이 없습니다.",
    "details": {
      "reason": "not_post_owner",
      "resource": "post",
      "id_field": "post_id",
      "id": "post_123"
    }
  }
}
```

**Response (404 Not Found)**

```json
{
  "status": "error",
  "error": {
    "code": "NOT_FOUND",
    "message": "요청한 리소스를 찾을 수 없습니다.",
    "details": {
      "resource": "post",
      "id_field": "post_id",
      "id": "post_999"
    }
  }
}
```

---

### 게시글 작성

**POST** `/posts`

로그인한 사용자가 새로운 게시글을 작성합니다. 요청 본문에 title, content를 포함해야 하며, 생성에 성공하면 게시글 ID와 생성 시간이 자동으로 할당됩니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Content-Type  | string | O  | 요청 데이터를 application/json 형태로 전송합니다.                                       |
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Request Body**

| 필드      | 타입     | 필수 | 설명                         |
|---------|--------|----|----------------------------|
| title   | string | O  | 게시글 제목입니다. 1~50자 제한이 있습니다. |
| content | string | O  | 게시글 내용입니다. 빈 값을 넣을 수 없습니다. |

**Request**

```json
{
  "title": "첫 번째 게시글",
  "content": "게시글 내용입니다."
}
```

**Response (201 Created)**

```json
{
  "status": "success",
  "data": {
    "id": "post_125",
    "author": "user_123",
    "title": "첫 번째 게시글",
    "content": "게시글 내용입니다.",
    "view_count": 0,
    "like_count": 0,
    "created_at": "2026-01-04T12:10:00Z"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "content",
      "reason": "missing_or_empty",
      "value": ""
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

---

### 회원 탈퇴

**DELETE** `/users/me`

인증된 회원의 요청에 따라 계정을 탈퇴 처리합니다. 탈퇴된 계정은 재사용할 수 없으며, 회원 데이터는 폐기됩니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Response (204 No Content)**

```json
204 No Content
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

---

### 프로필 수정

**PATCH** `/users/me`

로그인 된 회원은 본인의 프로필에서 닉네임, 프로필 이미지, 비밀번호를 변경할 수 있습니다.

**Request Headers**

| 헤더            | 타입     | 필수 | 설명                                                                        |
|---------------|--------|----|---------------------------------------------------------------------------|
| Content-Type  | string | O  | 요청 데이터를 `application/json` 형태로 전송합니다.                                     |
| Authorization | string | O  | Bearer 토큰 형식의 인증 정보. 로그인 시 발급받은 Access Token을 `Bearer {token}` 형태로 전달합니다. |

**Request Body**

| 필드          | 타입     | 필수 | 설명                                          |
|-------------|--------|----|---------------------------------------------|
| nickname    | string | X  | 닉네임 규칙을 준수한 새로운 닉네임을 입력받으면 기존 데이터를 교체합니다.   |
| password    | string | X  | 비밀번호 규칙을 준수한 새로운 비밀번호를 입력받으면 기존 데이터를 교체합니다. |
| profile_img | string | X  | 새로운 프로필 사진을 입력받으면 기존 데이터를 교체합니다.            |

**Request**

```json
{
  "nickname": "new123",
  "password": "Newpassword!1",
  "profile_img": "/images/profiles/new.png"
}
```

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "id": "user_123",
    "nickname": "new123",
    "profile_img": "/images/profiles/new.png"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "body",
      "reason": "no_fields_to_update",
      "value": {}
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "missing_or_invalid_token"
    }
  }
}
```

**Response (422 Validation Error)**

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값이 유효하지 않습니다.",
    "details": {
      "field": "nickname",
      "reason": "invalid_format",
      "value": "닉네임!!"
    }
  }
}
```

---

### 로그인

**POST** `/auth/tokens`

등록된 회원 정보 기반으로 로그인을 수행합니다. 요청 본문에 필수 필드인 `email`, `password`를 입력해야하며, 인증에 성공하면 자동으로 access_token이 발급됩니다.

**Request Headers**

| 헤더           | 타입     | 필수 | 설명                                    |
|--------------|--------|----|---------------------------------------|
| Content-Type | string | O  | 요청 데이터를 `application/json` 형태로 전송합니다. |

**Request Body**

| 필드       | 타입     | 필수 | 설명                                                    |
|----------|--------|----|-------------------------------------------------------|
| email    | string | O  | 로그인에 사용할 email 입니다. 회원가입 시 등록한 email과 일치해야 합니다.       |
| password | string | O  | 로그인에 사용할 password 입니다. 회원가입 시 등록한 password와 일치해야 합니다. |

**Request**

```json
{
  "email": "example@gmail.com",
  "password": "Password12@"
}
```

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {
    "access_token": "ewkjrh23",
    "user": {
      "id": "user_123",
      "nickname": "user123"
    }
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "password",
      "reason": "missing",
      "value": null
    }
  }
}
```

**Response (401 Unauthorized)**

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증되지 않은 회원입니다.",
    "details": {
      "reason": "invalid_credentials"
    }
  }
}
```

---

### 회원가입

**POST** `/users`

새로운 회원을 생성합니다. 요청 본문에 필수 필드인 `email`, `password`, `nickname`을 포함해야 하며, `profile_img`는 선택적으로 포함할 수 있습니다. 생성에 성공하면 자동으로 고유
ID와 생성 시간이 할당됩니다. 동일한 닉네임도 생성 가능하며, ID로 구분됩니다.

**Request Headers**

| 헤더           | 타입     | 필수 | 설명                                    |
|--------------|--------|----|---------------------------------------|
| Content-Type | string | O  | 요청 데이터를 `application/json` 형태로 전송합니다. |

**Request Body**

| 필드                                                                                                                   | 타입     | 필수 | 설명                                                                                                                                                                                                                              |
|----------------------------------------------------------------------------------------------------------------------|--------|----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| email                                                                                                                | string | O  | 회원가입 시 필요한 이메일 입니다. 1자 이상 255자 이하의 문자열이어야 하며, 유효한 이메일 형식을 입력해야합니다. 같은 이메일을 가진 리소스는 생성 불가능합니다.                                                                                                                                   |
| password                                                                                                             | string | O  | 회원가입 시 필요한 비밀번호입니다. 비밀번호 규칙을 준수해야합니다.                                                         <br> - 비밀번호 규칙: 8~16자의 영문 대소문자, 숫자 및 특수문자 사용 (사용 가능한 특수문자 32자 : ! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ ₩ ] ^ _ ` { \| } ~) |
| nickname                                                                                                             | string | O  | 회원이 보게되는 닉네임 입니다. 1~10자의 영문 대소문자 및 숫자로 구성된 문자열입니다. 다른 회원과 중복 가능합니다.                                                                                                                                                             |
| profile_img                                                                                                          | string | X  | 회원을 대표하는 프로필 이미지를 나타내며, 이미지의 서버 내부 저장 `path` 입니다.                                                                                                                                                                               |

**Request Example**

```json
{
  "email": "example@gmail.com",
  "password": "Password12@",
  "nickname": "user123",
  "profile_img": "/images/profiles/user123.png"
}
```

**Response (201 Created)**

```json
{
  "status": "success",
  "data": {
    "id": "user_123",
    "nickname": "user123",
    "created_at": "2026-01-04T12:00:00Z"
  }
}
```

**Response (400 Bad Request)**

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "잘못된 요청입니다.",
    "details": {
      "field": "password",
      "reason": "missing",
      "value": null
    }
  }
}
```

**Response (409 Conflict)**

```json
{
  "status": "error",
  "error": {
    "code": "CONFLICT",
    "message": "이미 존재하는 사용자입니다.",
    "details": {
      "field": "email",
      "reason": "already_exists",
      "value": "test@example.com"
    }
  }
}
```

**Response (422 Validation Error)**

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값이 유효하지 않습니다.",
    "details": {
      "field": "email",
      "reason": "invalid_format",
      "value": "test@"
    }
  }
}
```

---
