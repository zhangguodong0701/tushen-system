# routers/drawings.py - 图纸管理 API
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os, uuid

from models import get_db, User, Order, Drawing
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["图纸"])

UPLOAD_DIR = "./uploads"


def _save_file(file: UploadFile) -> str:
    """安全保存文件：检查扩展名 + MIME 类型"""
    ext = os.path.splitext(file.filename)[1].lower()
    ALLOWED = {".pdf", ".dwg", ".dxf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"}
    if ext not in ALLOWED:
        raise HTTPException(400, f"不支持的文件类型：{ext}")
    
    # 读取文件头进行 MIME 类型检测
    content = file.file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "文件大小超过 50MB")
    
    # MIME 类型白名单校验
    mime_whitelist = {
        ".pdf": "application/pdf",
        ".dwg": "application/acad",
        ".dxf": "application/dxf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".zip": "application/zip",
        ".rar": "application/vnd.rar"
    }
    
    # 读取文件头字节进行 MIME 检测
    header = content[:16]
    detected_mime = None
    
    if header[:8] == b'%PDF':
        detected_mime = "application/pdf"
    elif header[:8] == b'\x89PNG\r\n\x1a\n':
        detected_mime = "image/png"
    elif header[:3] == b'\xff\xd8\xff':
        detected_mime = "image/jpeg"
    elif header[:6] == b'GIF87a' or header[:6] == b'GIF89a':
        detected_mime = "image/gif"
    elif header[:4] == b'PK\x03\x04':
        detected_mime = "application/zip"  # ZIP/DOCX/XLSX
    elif header[:5] == b'%DWG':
        detected_mime = "application/acad"  # DWG
    
    # 如果是文档类（DOCX/XLSX 等），通过扩展名信任（MIME 检测复杂）
    if ext in {".docx", ".xlsx"} and detected_mime == "application/zip":
        detected_mime = mime_whitelist.get(ext)
    
    # 验证 MIME 类型
    expected_mime = mime_whitelist.get(ext)
    if expected_mime and detected_mime and detected_mime != expected_mime:
        raise HTTPException(400, f"文件类型不匹配：扩展名为{ext}，但实际类型为{detected_mime}")
    
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
        f.write(content)
    return f"/uploads/{fname}"


@router.post("/orders/{order_id}/drawings")
def upload_drawing(order_id: int, file: UploadFile = File(...), version: str = Form(None),
                    version_num: int = Form(None), group_id: int = Form(None),
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.seller_id != current_user.id:
        raise HTTPException(403, "只有订单承接方（乙方）才能上传图纸")

    # 如果是上传新版本（指定了 group_id），找到当前最大版本号
    if group_id:
        max_version = db.query(Drawing).filter(
            Drawing.group_id == group_id
        ).order_by(Drawing.version_num.desc()).first()
        if max_version:
            version_num = max_version.version_num + 1
            version = f"V{version_num}"
    else:
        # 新图纸，找同名文件的最大版本
        existing_same_name = db.query(Drawing).filter(
            Drawing.order_id == order_id,
            Drawing.filename == file.filename
        ).order_by(Drawing.version_num.desc()).first()

        if existing_same_name:
            # 同一文件已有版本，作为新版本上传
            group_id = existing_same_name.group_id or existing_same_name.id
            version_num = existing_same_name.version_num + 1
            version = f"V{version_num}"
        else:
            # 全新的图纸
            existing_count = db.query(Drawing).filter(Drawing.order_id == order_id).count()
            version_num = 1
            version = "V1"

    drawing = Drawing(
        order_id=order_id,
        uploader_id=current_user.id,
        filename=file.filename,
        file_url=_save_file(file),
        version=version,
        version_num=version_num,
        group_id=group_id
    )
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return {"message": "图纸上传成功", "drawing_id": drawing.id, "version": version}


@router.get("/orders/{order_id}/drawings")
def list_drawings(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取订单下所有图纸（按 group_id 分组）"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    # 只允许订单参与者查看
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "无权查看此订单的图纸")
    
    drawings = db.query(Drawing).filter(Drawing.order_id == order_id).order_by(Drawing.created_at.desc()).all()
    # 按 group_id 分组
    groups = {}
    for d in drawings:
        gid = d.group_id or d.id
        if gid not in groups:
            groups[gid] = []
        groups[gid].append(d)
    
    result = []
    for gid, items in groups.items():
        items.sort(key=lambda x: x.version_num, reverse=True)
        latest = items[0]
        user = db.query(User).filter(User.id == latest.uploader_id).first()
        result.append({
            "id": latest.id,
            "group_id": gid,
            "filename": latest.filename,
            "file_url": latest.file_url,
            "version": latest.version,
            "version_num": latest.version_num,
            "version_count": len(items),
            "comments": latest.comments,
            "uploader_name": user.real_name if user else "",
            "created_at": str(latest.created_at)
        })
    return result


@router.get("/orders/{order_id}/drawings/{group_id}/versions")
def list_drawing_versions(order_id: int, group_id: int,
                          current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取某个图纸的所有版本"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "无权查看此订单的图纸")
    
    drawings = db.query(Drawing).filter(Drawing.group_id == group_id).order_by(Drawing.version_num.desc()).all()
    if not drawings:
        raise HTTPException(404, "未找到该图纸的版本")
    
    versions = []
    for d in drawings:
        user = db.query(User).filter(User.id == d.uploader_id).first()
        versions.append({
            "id": d.id,
            "version": d.version,
            "version_num": d.version_num,
            "file_url": d.file_url,
            "comments": d.comments or "",
            "comment_images": d.comment_images or "",
            "uploader_name": user.real_name if user else "",
            "created_at": str(d.created_at)
        })
    
    return {
        "filename": drawings[0].filename,
        "group_id": group_id,
        "versions": versions
    }


@router.post("/drawings/{drawing_id}/comment")
def add_drawing_comment(drawing_id: int, comments: str = Form(...),
                        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """给图纸添加评论/修改意见"""
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(404, "图纸不存在")
    
    order = db.query(Order).filter(Order.id == drawing.order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    
    # 只允许订单参与者评论
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "无权评论此图纸")
    
    drawing.comments = comments
    db.commit()
    return {"message": "评论已保存"}
