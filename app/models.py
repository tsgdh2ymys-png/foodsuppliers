"""Модель данных поставщика.

Поля разделены на три группы:
  1. Идентификация и поиск: name, category, city, regions, description.
  2. Контакты и источник: website, phone, email, source.
  3. Данные для сравнения и скоринга: min_order(_num), price(_num),
     certificates / has_certificates, delivery / has_delivery.

Числовые *_num поля и булевы has_* — машинно-сравнимые значения для скоринга.
Где данных нет (типично для реальных B2B-поставщиков — «цена по запросу»),
поле = None, и в скоринге критерий честно помечается как «нет данных».
"""
from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- идентификация и поиск ---
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    regions: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    # --- контакты и источник ---
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    source: Mapped[str] = mapped_column(String(400), default="")

    # --- данные для сравнения / скоринга ---
    min_order: Mapped[str | None] = mapped_column(String(150), nullable=True)
    min_order_num: Mapped[float | None] = mapped_column(Float, nullable=True)
    price: Mapped[str | None] = mapped_column(String(150), nullable=True)
    price_num: Mapped[float | None] = mapped_column(Float, nullable=True)
    certificates: Mapped[str | None] = mapped_column(String(300), nullable=True)
    has_certificates: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    delivery: Mapped[str | None] = mapped_column(String(300), nullable=True)
    has_delivery: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # --- редакционный комментарий (общая заметка о поставщике) ---
    comment: Mapped[str] = mapped_column(Text, default="")

    # --- метаданные / пользовательское состояние ---
    is_real: Mapped[bool] = mapped_column(Boolean, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
