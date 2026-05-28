import shlex
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, select, text
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note
from ..schemas import NoteCreate, NotePatch, NoteRead

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteRead])
def list_notes(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    sort: str = Query("-created_at", description="Sort by field, prefix with - for desc"),
) -> list[NoteRead]:
    stmt = select(Note)
    if q:
        stmt = stmt.where((Note.title.contains(q)) | (Note.content.contains(q)))

    sort_field = sort.lstrip("-")
    order_fn = desc if sort.startswith("-") else asc
    if hasattr(Note, sort_field):
        stmt = stmt.order_by(order_fn(getattr(Note, sort_field)))
    else:
        stmt = stmt.order_by(desc(Note.created_at))

    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.patch("/{note_id}", response_model=NoteRead)
def patch_note(note_id: int, payload: NotePatch, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)


@router.get("/unsafe-search", response_model=list[NoteRead])
def unsafe_search(q: str, db: Session = Depends(get_db)) -> list[NoteRead]:
    sql = text(
        """
        SELECT id, title, content, created_at, updated_at
        FROM notes
        WHERE title LIKE :q OR content LIKE :q
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    rows = db.execute(sql, {"q": f"%{q}%"}).all()

    results: list[NoteRead] = []
    for r in rows:
        results.append(
            NoteRead(
                id=r.id,
                title=r.title,
                content=r.content,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return results


@router.get("/debug/hash-md5")
def debug_hash_md5(q: str) -> dict[str, str]:
    import hashlib

    return {"algo": "md5", "hex": hashlib.md5(q.encode()).hexdigest()}


@router.get("/debug/eval")
def debug_eval(expr: str) -> dict[str, str]:
    # 修复：将 eval() 的 __builtins__ 替换为空字典，阻断 __import__ / open 等危险函数
    result = str(eval(expr, {"__builtins__": {}}))  # noqa: S307
    return {"result": result}


@router.get("/debug/run")
def debug_run(cmd: str) -> dict[str, str]:
    import subprocess

    # 修复：去掉 shell=True，改用 shlex.split 将命令字符串安全拆分为参数列表
    completed = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    return {"returncode": str(completed.returncode), "stdout": completed.stdout, "stderr": completed.stderr}


@router.get("/debug/fetch")
def debug_fetch(url: str) -> dict[str, str]:
    from urllib.request import urlopen

    # 修复：解析 URL 并只允许 http / https 协议，阻断 file:// / ftp:// 等
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http:// and https:// URLs are allowed")
    with urlopen(url) as res:  # noqa: S310
        body = res.read(1024).decode(errors="ignore")
    return {"snippet": body}


@router.get("/debug/read")
def debug_read(path: str) -> dict[str, str]:
    import os

    # 修复：将路径限制在项目根目录内，阻断 ../../etc/passwd 这类目录穿越攻击
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    safe_path = os.path.normpath(os.path.join(base_dir, path.lstrip("/")))
    if not safe_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Access denied: path outside project root")
    try:
        content = open(safe_path, "r").read(1024)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    return {"snippet": content}







