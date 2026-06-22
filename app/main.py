"""FastAPI-приложение: поиск, карточка и сравнение поставщиков."""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Supplier
from .seed_data import seed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed()
    yield


app = FastAPI(title="FoodSuppliers — поиск и сравнение поставщиков", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def _distinct(db: Session, column):
    return [r[0] for r in db.execute(select(column).distinct().order_by(column)).all()]


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str = "",
    category: str = "",
    city: str = "",
    sort: str = "relevance",
    only_fav: int = 0,
    kind: str = "",
    db: Session = Depends(get_db),
):
    stmt = select(Supplier)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            Supplier.name.ilike(like)
            | Supplier.description.ilike(like)
            | Supplier.category.ilike(like)
            | Supplier.city.ilike(like)
            | Supplier.regions.ilike(like)
        )
    if category:
        stmt = stmt.where(Supplier.category == category)
    if city:
        stmt = stmt.where(Supplier.city == city)
    if only_fav:
        stmt = stmt.where(Supplier.is_favorite.is_(True))
    if kind == "real":
        stmt = stmt.where(Supplier.is_real.is_(True))
    elif kind == "demo":
        stmt = stmt.where(Supplier.is_real.is_(False))

    # Сортировка. Для цены/мин.заказа пустые значения отправляем в конец.
    if sort == "price":
        stmt = stmt.order_by(Supplier.price_num.is_(None), Supplier.price_num.asc())
    elif sort == "min_order":
        stmt = stmt.order_by(Supplier.min_order_num.is_(None), Supplier.min_order_num.asc())
    else:
        # relevance: сначала с заполненными данными, затем по имени
        stmt = stmt.order_by(Supplier.is_real.desc(), Supplier.name.asc())

    suppliers = db.execute(stmt).scalars().all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "suppliers": suppliers,
            "categories": _distinct(db, Supplier.category),
            "cities": _distinct(db, Supplier.city),
            "q": q,
            "category": category,
            "city": city,
            "sort": sort,
            "only_fav": only_fav,
            "kind": kind,
            "total": len(suppliers),
            "fav_count": db.query(Supplier).filter(Supplier.is_favorite.is_(True)).count(),
            "real_total": db.query(Supplier).filter(Supplier.is_real.is_(True)).count(),
            "demo_total": db.query(Supplier).filter(Supplier.is_real.is_(False)).count(),
        },
    )


@app.get("/supplier/{supplier_id}", response_class=HTMLResponse)
def supplier_detail(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    s = db.get(Supplier, supplier_id)
    if not s:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("supplier.html", {"request": request, "s": s})


@app.post("/supplier/{supplier_id}/favorite")
def toggle_favorite(
    supplier_id: int, next: str = Form("/"), db: Session = Depends(get_db)
):
    s = db.get(Supplier, supplier_id)
    if s:
        s.is_favorite = not s.is_favorite
        db.commit()
    return RedirectResponse(next or "/", status_code=303)


@app.post("/supplier/{supplier_id}/notes")
def save_notes(
    supplier_id: int, notes: str = Form(""), next: str = Form("/"), db: Session = Depends(get_db)
):
    s = db.get(Supplier, supplier_id)
    if s:
        s.notes = notes.strip()
        db.commit()
    return RedirectResponse(next or f"/supplier/{supplier_id}", status_code=303)


@app.get("/compare", response_class=HTMLResponse)
def compare(request: Request, ids: str = "", db: Session = Depends(get_db)):
    id_list = []
    for part in ids.split(","):
        part = part.strip()
        if part.isdigit():
            id_list.append(int(part))
    suppliers = (
        db.execute(select(Supplier).where(Supplier.id.in_(id_list))).scalars().all()
        if id_list
        else []
    )
    # сохраняем порядок, в котором пользователь их выбрал
    order = {sid: i for i, sid in enumerate(id_list)}
    suppliers.sort(key=lambda s: order.get(s.id, 999))

    return templates.TemplateResponse(
        "compare.html",
        {"request": request, "suppliers": suppliers},
    )


@app.get("/add", response_class=HTMLResponse)
def add_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "add.html",
        {"request": request, "categories": _distinct(db, Supplier.category)},
    )


@app.post("/add")
def add_supplier(
    name: str = Form(...),
    category: str = Form(...),
    city: str = Form(""),
    regions: str = Form(""),
    description: str = Form(""),
    website: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    min_order: str = Form(""),
    min_order_num: str = Form(""),
    price: str = Form(""),
    price_num: str = Form(""),
    certificates: str = Form(""),
    has_certificates: str = Form(""),
    delivery: str = Form(""),
    has_delivery: str = Form(""),
    db: Session = Depends(get_db),
):
    def num(v):
        try:
            return float(str(v).replace(" ", "").replace(",", "."))
        except (TypeError, ValueError):
            return None

    s = Supplier(
        name=name.strip(),
        category=category.strip() or "Прочее",
        city=city.strip(),
        regions=regions.strip(),
        description=description.strip(),
        website=website.strip() or None,
        phone=phone.strip() or None,
        email=email.strip() or None,
        source="Добавлено вручную",
        min_order=min_order.strip() or None,
        min_order_num=num(min_order_num),
        price=price.strip() or None,
        price_num=num(price_num),
        certificates=certificates.strip() or None,
        has_certificates=True if has_certificates == "on" else None,
        delivery=delivery.strip() or None,
        has_delivery=True if has_delivery == "on" else None,
        is_real=False,
    )
    db.add(s)
    db.commit()
    return RedirectResponse(f"/supplier/{s.id}", status_code=303)
