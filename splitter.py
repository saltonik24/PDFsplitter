from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass
from typing import List, Tuple, Optional

from pypdf import PdfReader, PdfWriter


@dataclass
class SplitPlan:
    pages_per_doc: int
    filenames: List[str]


def _normalize_filename(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    # Запрещаем пути, чтобы не было "../"
    name = name.replace("\\", "/").split("/")[-1]
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def split_pdf_to_zip_bytes(
    pdf_bytes: bytes,
    plan: SplitPlan,
    strict_pages: bool = True,
) -> Tuple[bytes, List[str]]:
    """
    Режет PDF на части согласно plan (pages_per_doc + filenames),
    возвращает ZIP как bytes и список логов.
    """
    logs: List[str] = []
    if plan.pages_per_doc <= 0:
        raise ValueError("pages_per_doc должен быть больше 0")

    filenames = [_normalize_filename(x) for x in plan.filenames]
    filenames = [x for x in filenames if x]  # убираем пустые
    if not filenames:
        raise ValueError("Список имен файлов пуст")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    expected_pages = len(filenames) * plan.pages_per_doc

    logs.append(f"Всего страниц в PDF: {total_pages}")
    logs.append(f"Файлов по списку: {len(filenames)}")
    logs.append(f"Страниц на документ: {plan.pages_per_doc}")
    logs.append(f"Ожидаемо страниц: {expected_pages}")

    if strict_pages and total_pages != expected_pages:
        raise ValueError(
            f"Количество страниц не совпадает: PDF={total_pages}, ожидаемо={expected_pages}."
        )

    # Если strict_pages=False, режем пока хватает страниц
    max_docs = min(len(filenames), total_pages // plan.pages_per_doc)
    if max_docs < len(filenames):
        logs.append(
            f"Предупреждение: страниц не хватает на все имена. Будет создано файлов: {max_docs}"
        )

    out_zip = io.BytesIO()
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i in range(max_docs):
            start = i * plan.pages_per_doc
            end = start + plan.pages_per_doc

            writer = PdfWriter()
            for p in range(start, end):
                writer.add_page(reader.pages[p])

            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            pdf_out.seek(0)

            zf.writestr(filenames[i], pdf_out.read())
            logs.append(f"Создано: {filenames[i]} (страницы {start+1}-{end})")

    out_zip.seek(0)
    return out_zip.read(), logs
