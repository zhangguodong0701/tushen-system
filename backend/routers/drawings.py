# routers/drawings.py - 图纸管理 API
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os, uuid

from models import get_db, User, Order, Drawing
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["图纸"])

UPLOAD_DIR = "./uploads"


def _save_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    ALLOWED = {".pdf", ".dwg", ".dxf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"}
    if ext not in ALLOWED:
        raise HTTPException(400, f"不支持的文件类型: {ext}")
    content = file.file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "文件大小超过50MB")
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

    # 如果是上传新版本（指定了group_id），找到当前最大版本号
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
            version = f"V{existing_count + 1}"

    url = _save_file(file)
    drawing = Drawing(
        order_id=order_id,
        uploader_id=current_user.id,
        filename=file.filename,
        file_url=url,
        version=version,
        version_num=version_num,
        group_id=group_id  # 如果是新版，group_id指向主版本；如果是新图纸，稍后更新
    )

    # 如果是全新图纸且还没分配group_id，用自己的id
    if not drawing.group_id:
        db.add(drawing)
        db.commit()
        db.refresh(drawing)
        # 把自己设为group_id
        drawing.group_id = drawing.id
        db.commit()
        db.refresh(drawing)
    else:
        db.add(drawing)
        db.commit()
        db.refresh(drawing)

    return {
        "id": drawing.id,
        "filename": drawing.filename,
        "file_url": drawing.file_url,
        "version": drawing.version,
        "version_num": drawing.version_num,
        "group_id": drawing.group_id,
        "created_at": str(drawing.created_at)
    }


@router.get("/drawings")
def list_my_drawings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(
        (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
    ).all()
    order_ids = [o.id for o in orders]
    if not order_ids:
        return []
    drawings = db.query(Drawing).filter(Drawing.order_id.in_(order_ids)).order_by(Drawing.created_at.desc()).all()
    result = []
    for d in drawings:
        order = next((o for o in orders if o.id == d.order_id), None)
        order_title = f"订单 {d.order_id}"
        if order and order.demand:
            order_title = order.demand.title
        elif order:
            from models import Demand
            demand = db.query(Demand).filter(Demand.id == order.demand_id).first()
            if demand:
                order_title = demand.title
        result.append({
            "id": d.id, "name": d.filename, "filename": d.filename,
            "file_url": d.file_url, "order_id": d.order_id,
            "order_title": order_title,
            "version": d.version,
            "version_num": d.version_num,
            "group_id": d.group_id,
            "comments": d.comments,
            "comment_images": d.comment_images,
            "uploader_name": d.uploader.real_name if d.uploader else "",
            "created_at": str(d.created_at)
        })
    return result


@router.get("/orders/{order_id}/drawings")
def list_drawings(order_id: int, db: Session = Depends(get_db)):
    drawings = db.query(Drawing).filter(Drawing.order_id == order_id).order_by(Drawing.created_at.desc()).all()
    return [{
        "id": d.id,
        "filename": d.filename,
        "file_url": d.file_url,
        "version": d.version,
        "version_num": d.version_num,
        "group_id": d.group_id,
        "comments": d.comments,
        "comment_images": d.comment_images,
        "uploader_name": d.uploader.real_name if d.uploader else "",
        "created_at": str(d.created_at)
    } for d in drawings]


@router.put("/drawings/{drawing_id}/comments")
def add_comment(drawing_id: int, comments: str = Form(""), comment_images: str = Form(""),
               current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(404, "图纸不存在")
    order = db.query(Order).filter(Order.id == drawing.order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能提交修改意见")
    drawing.comments = comments
    if comment_images:
        drawing.comment_images = comment_images
    db.commit()
    return {"message": "意见已保存"}


@router.post("/drawings/{drawing_id}/upload-comment-img")
def upload_comment_img(drawing_id: int, file: UploadFile = File(...),
                       current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(404, "图纸不存在")
    order = db.query(Order).filter(Order.id == drawing.order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能上传意见图片")
    url = _save_file(file)
    return {"url": url}


# ================ 版本管理 API ================

@router.get("/orders/{order_id}/drawing-groups")
def list_drawing_groups(order_id: int, current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """获取订单下的图纸版本组列表（每个图纸只返回最新版本）"""
    # 验证用户权限
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "无权访问此订单")

    # 获取所有图纸，按 group_id 分组，取每个组的最新版本
    all_drawings = db.query(Drawing).filter(
        Drawing.order_id == order_id
    ).order_by(Drawing.group_id, Drawing.version_num.desc()).all()

    # 按 group_id 分组，每组只取 version_num 最大的
    groups = {}
    for d in all_drawings:
        if d.group_id not in groups:
            groups[d.group_id] = d

    # 构建结果
    result = []
    for group_id, latest in groups.items():
        # 统计该组总版本数
        version_count = db.query(Drawing).filter(Drawing.group_id == group_id).count()
        result.append({
            "id": latest.id,
            "group_id": group_id,
            "filename": latest.filename,
            "file_url": latest.file_url,
            "version": latest.version,
            "version_num": latest.version_num,
            "version_count": version_count,
            "comments": latest.comments,
            "uploader_name": latest.uploader.real_name if latest.uploader else "",
            "created_at": str(latest.created_at)
        })

    # 按最新更新时间排序
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return result


@router.get("/drawings/{drawing_id}/versions")
def get_drawing_versions(drawing_id: int, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """获取某个图纸的所有版本历史"""
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(404, "图纸不存在")

    # 验证用户权限
    order = db.query(Order).filter(Order.id == drawing.order_id).first()
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "无权访问此图纸")

    # 获取同组的所有版本
    versions = db.query(Drawing).filter(
        Drawing.group_id == drawing.group_id
    ).order_by(Drawing.version_num.desc()).all()

    # 获取需求标题
    order_title = f"订单 {drawing.order_id}"
    if order.demand:
        order_title = order.demand.title

    return {
        "filename": drawing.filename,
        "order_title": order_title,
        "group_id": drawing.group_id,
        "versions": [{
            "id": v.id,
            "version": v.version,
            "version_num": v.version_num,
            "file_url": v.file_url,
            "comments": v.comments,
            "comment_images": v.comment_images,
            "uploader_name": v.uploader.real_name if v.uploader else "",
            "created_at": str(v.created_at)
        } for v in versions]
    }
