from fastapi import FastAPI

app = FastAPI()


# ----- USERS ----- #

# signup
@app.post("/users")
async def create_user(user: dict):
    pass


# login
@app.post("/auth/tokens")
async def get_auth_tokens():
    pass


# edit profile
# Depends를 활용한 의존성 주입으로 구현
@app.patch("/users/me")
async def update_my_profile():
    pass


# get my profile
# Depends를 활용한 의존성 주입으로 구현
@app.get("/users/me")
async def get_my_profile():
    pass


# delete account
# Depends를 활용한 의존성 주입으로 구현
@app.delete("/users/me")
async def delete_my_account():
    pass


# get a specific user
@app.get("/users/{user_id}")
async def get_specific_user(user_id: int):
    pass


# ----- POSTS ----- #

# List, search, sort posts
@app.get("/posts")
async def get_posts(
        page: int = 1,
        limit: int = 20,
        q: str | None = None,
        sort: str = "created_at",
        order: str = "desc"
):
    pass

# post new post
@app.post("/posts")
async def create_post(post: dict):
    pass


# post list I wrote
@app.get("/posts/me")
async def get_posts_mine(page: int = 1, limit: int = 20):
    pass


# get a single post
@app.get("/posts/{post_id}")
async def get_single_post(post_id: int):
    pass


# edit post
@app.patch("/posts/{post_id}")
async def update_post(post_id: int):
    pass


# delete post
@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    pass


# ----- COMMENTS ----- #

# List all comments for a post
@app.get("/posts/{post_id}/comments")
async def get_comments(post_id: int, page: int = 1, limit: int = 10):
    pass


# post comment
@app.post("/posts/{post_id}/comments")
async def post_comment(post_id: int):
    pass

# edit comment
@app.patch("/posts/{post_id}/comments/{comment_id}")
async def update_comment(post_id: int, comment_id: int):
    pass

# delete comment
@app.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int):
    pass


# comment list I wrote
@app.get("/comments/me")
async def get_comments_mine(page: int = 1, limit: int = 20):
    pass


# ----- LIKES ----- #

# register like
@app.post("/posts/{post_id}/likes")
async def post_like(post_id: int):
    pass

# delete like
@app.delete("/posts/{post_id}/likes")
async def delete_like(post_id: int):
    pass

# check like status
@app.get("/posts/{post_id}/likes")
async def get_likes_status(post_id: int):
    pass

# post list I liked
@app.get("/posts/liked")
async def get_posts_liked(page: int = 1, limit: int = 20):
    pass
