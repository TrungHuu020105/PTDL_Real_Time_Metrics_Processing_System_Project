"""Chat support routes for user bot + admin handoff."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    ChatSendRequest,
    ChatEscalateRequest,
    ChatAdminReplyRequest,
    ChatConversationListResponse,
    ChatMessagesListResponse,
    ChatIssueTemplateCreate,
    ChatIssueTemplateUpdate,
)
from app.api.routes_auth import get_current_user
from app import crud
from app.services.chat_service import generate_user_bot_reply

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _conversation_to_response(db: Session, conversation):
    messages = crud.list_chat_messages(db, conversation.id)
    last_preview = messages[-1].content[:120] if messages else ""
    unread_for_user = len([m for m in messages if m.sender_type in {"admin", "system"}])
    unread_for_admin = len([m for m in messages if m.sender_type == "user"])
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "assigned_admin_id": conversation.assigned_admin_id,
        "status": conversation.status,
        "subject": conversation.subject,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "last_message_preview": last_preview,
        "unread_for_user": unread_for_user,
        "unread_for_admin": unread_for_admin,
    }


def _validate_conversation_access(conversation, current_user: User):
    if current_user.role == "admin":
        return
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this conversation")


def _ensure_default_issue_templates(db: Session):
    rows = crud.list_chat_issue_templates(db, active_only=False)
    if rows:
        return
    defaults = [
        ("Sensor no data", "Sensor khong gui du lieu hoac mat ket noi", 1),
        ("Value too high", "Gia tri do duoc cao hon muc binh thuong", 2),
        ("Value too low", "Gia tri do duoc thap hon muc binh thuong", 3),
        ("Too many alerts", "Canh bao lap lai nhieu lan trong thoi gian ngan", 4),
        ("Need setup help", "Can huong dan cau hinh sensor, nguong canh bao, dashboard", 5),
        ("Other", "Van de khac, nguoi dung se mo ta them", 999),
    ]
    for title, desc, order in defaults:
        crud.create_chat_issue_template(
            db=db,
            title=title,
            description=desc,
            created_by=None,
            sort_order=order,
            is_active=True,
        )


@router.get("/conversations", response_model=ChatConversationListResponse)
async def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        conversations = crud.list_admin_chat_conversations(db, status_filter=None)
    else:
        conversations = crud.list_user_chat_conversations(db, current_user.id)
    items = [_conversation_to_response(db, c) for c in conversations]
    return {"conversations": items, "count": len(items)}


@router.get("/issue-templates")
async def list_issue_templates(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_default_issue_templates(db)
    if include_inactive and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only for inactive templates")
    rows = crud.list_chat_issue_templates(db, active_only=not include_inactive)
    return {"items": rows, "count": len(rows)}


@router.post("/admin/issue-templates")
async def create_issue_template(
    payload: ChatIssueTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    row = crud.create_chat_issue_template(
        db=db,
        title=payload.title,
        description=payload.description,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    return {"success": True, "item": row}


@router.patch("/admin/issue-templates/{template_id}")
async def update_issue_template(
    template_id: int,
    payload: ChatIssueTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    row = crud.get_chat_issue_template(db, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    updated = crud.update_chat_issue_template(db, row, data)
    return {"success": True, "item": updated}


@router.delete("/admin/issue-templates/{template_id}")
async def delete_issue_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    row = crud.get_chat_issue_template(db, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    crud.delete_chat_issue_template(db, row)
    return {"success": True}


@router.get("/admin/conversations", response_model=ChatConversationListResponse)
async def list_admin_conversations(
    status: str = Query("all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    conversations = crud.list_admin_chat_conversations(db, status_filter=status)
    items = [_conversation_to_response(db, c) for c in conversations]
    return {"conversations": items, "count": len(items)}


@router.get("/conversations/{conversation_id}", response_model=ChatMessagesListResponse)
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = crud.get_chat_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    _validate_conversation_access(conversation, current_user)

    messages = crud.list_chat_messages(db, conversation_id)
    return {
        "conversation": _conversation_to_response(db, conversation),
        "messages": messages,
        "count": len(messages),
    }


@router.post("/send")
async def send_message(
    payload: ChatSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = None
    if payload.conversation_id:
        conversation = crud.get_chat_conversation(db, payload.conversation_id)
    if not conversation:
        conversation = crud.create_chat_conversation(db, user_id=current_user.id, status="bot_active", subject="User support")
    _validate_conversation_access(conversation, current_user)

    user_message = crud.create_chat_message(
        db,
        conversation_id=conversation.id,
        sender_type="user",
        sender_id=current_user.id,
        content=payload.message.strip(),
    )

    if conversation.status in {"waiting_admin", "in_progress"}:
        return {
            "conversation_id": conversation.id,
            "status": conversation.status,
            "user_message": user_message,
            "bot_message": None,
        }

    bot_reply = generate_user_bot_reply(db=db, user=current_user, user_message=payload.message.strip())
    bot_message = crud.create_chat_message(
        db,
        conversation_id=conversation.id,
        sender_type="bot",
        content=bot_reply,
    )
    crud.update_chat_conversation_status(db, conversation, status="bot_active")
    return {
        "conversation_id": conversation.id,
        "status": "bot_active",
        "user_message": user_message,
        "bot_message": bot_message,
    }


@router.post("/escalate")
async def escalate_to_admin(
    payload: ChatEscalateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = None
    if payload.conversation_id:
        conversation = crud.get_chat_conversation(db, payload.conversation_id)
    if not conversation:
        conversation = crud.get_latest_user_chat_conversation(db, current_user.id)
    if not conversation:
        conversation = crud.create_chat_conversation(db, user_id=current_user.id, status="waiting_admin", subject="Need admin support")

    _validate_conversation_access(conversation, current_user)
    crud.update_chat_conversation_status(db, conversation, status="waiting_admin")

    reason = (payload.reason or "").strip()
    if reason:
        crud.create_chat_message(
            db,
            conversation_id=conversation.id,
            sender_type="user",
            sender_id=current_user.id,
            content=f"[Yêu cầu chat admin] {reason}",
        )

    system_message = crud.create_chat_message(
        db,
        conversation_id=conversation.id,
        sender_type="system",
        content="Yêu cầu đã được gửi đến admin. Vui lòng chờ admin phản hồi trong khung chat này.",
    )
    return {
        "conversation_id": conversation.id,
        "status": "waiting_admin",
        "system_message": system_message,
    }


@router.post("/admin/conversations/{conversation_id}/reply")
async def admin_reply(
    conversation_id: int,
    payload: ChatAdminReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    conversation = crud.get_chat_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    crud.update_chat_conversation_status(
        db,
        conversation,
        status="in_progress",
        assigned_admin_id=current_user.id,
    )
    admin_msg = crud.create_chat_message(
        db,
        conversation_id=conversation.id,
        sender_type="admin",
        sender_id=current_user.id,
        content=payload.message.strip(),
    )
    return {
        "conversation_id": conversation.id,
        "status": "in_progress",
        "admin_message": admin_msg,
    }


@router.post("/admin/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    conversation = crud.get_chat_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    crud.update_chat_conversation_status(db, conversation, status="closed")
    crud.create_chat_message(
        db,
        conversation_id=conversation.id,
        sender_type="system",
        content="Admin đã đóng cuộc hội thoại. Bạn có thể tiếp tục chat với bot hoặc mở yêu cầu mới.",
    )
    return {"success": True, "conversation_id": conversation.id, "status": "closed"}
