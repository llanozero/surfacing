"""视图状态（/api/view）：当前视图保存在服务端内存。"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/view", tags=["view"])

VALID_VIEWS = {"search", "nav", "plan", "browse", "tree"}
_current_view = "search"


class SwitchBody(BaseModel):
    view: str


@router.get("/current")
def get_current() -> dict:
    return {"view": _current_view}


@router.post("/switch")
def switch_view(body: SwitchBody) -> dict:
    global _current_view
    if body.view in VALID_VIEWS:
        _current_view = body.view
    return {"ok": True, "view": _current_view}
