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
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.seller_id != current_user.id:
        raise HTTPException(403, "只有订单承接方（乙方）才能上传图纸")
    if not version:
        existing = db.query(Drawing).filter(Drawing.order_id == order_id).count()
        version = f"V{existing + 1}"
    url = _save_file(file)
    drawing = Drawing(order_id=order_id, uploader_id=current_user.id,
                      filename=file.filename, file_url=url, version=version)
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return {"id": drawing.id, "filename": drawing.filename, "file_url": drawing.file_url,
            "version": drawing.version, "created_at": str(drawing.created_at)}


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
            "version": d.version, "comments": d.comments,
            "comment_images": d.comment_images,
            "uploader_name": d.uploader.real_name if d.uploader else "",
            "created_at": str(d.created_at)
        })
    return result


@router.get("/orders/{order_id}/drawings")
def list_drawings(order_id: int, db: Session = Depends(get_db)):
    drawings = db.query(Drawing).filter(Drawing.order_id == order_id).order_by(Drawing.created_at.desc()).all()
    return [{"id": d.id, "filename": d.filename, "file_url": d.file_url,
             "version": d.version, "comments": d.comments,
             "comment_images": d.comment_images,
             "uploader_name": d.uploader.real_name if d.uploader else "",
             "created_at": str(d.created_at)} for d in drawings]


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
