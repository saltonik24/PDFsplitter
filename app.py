import io
from typing import List

import streamlit as st
from splitter import SplitPlan, split_pdf_to_zip_bytes


# --- Функции чтения имен файлов ---

def read_names_from_txt(file_bytes: bytes) -> List[str]:
    text = file_bytes.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    return [x for x in lines if x]


def read_names_from_xlsx(file_bytes: bytes) -> List[str]:
    import pandas as pd

    df = pd.read_excel(io.BytesIO(file_bytes))
    if "filename" not in df.columns:
        raise ValueError("В Excel должна быть колонка с названием: filename")
    names = df["filename"].astype(str).tolist()
    names = [x.strip() for x in names if str(x).strip()]
    return names


# --- Интерфейс ---

st.set_page_config(page_title="PDF Splitter", page_icon="📄")

st.title("📄 Нарезка PDF на документы")

pages_per_doc = st.number_input(
    "Количество страниц в одном документе",
    min_value=1,
    value=3,
    step=1,
)

strict_pages = st.checkbox(
    "Строгое совпадение количества страниц",
    value=True,
)

pdf_file = st.file_uploader("Загрузи PDF", type=["pdf"])
names_file = st.file_uploader("Загрузи names.txt или names.xlsx", type=["txt", "xlsx"])


if st.button("Обработать", disabled=not (pdf_file and names_file)):
    try:
        pdf_bytes = pdf_file.read()
        nf_bytes = names_file.read()

        if names_file.name.lower().endswith(".txt"):
            filenames = read_names_from_txt(nf_bytes)
        elif names_file.name.lower().endswith(".xlsx"):
            filenames = read_names_from_xlsx(nf_bytes)
        else:
            raise ValueError("Поддерживаются только TXT или XLSX")

        plan = SplitPlan(
            pages_per_doc=int(pages_per_doc),
            filenames=filenames
        )

        zip_bytes, logs = split_pdf_to_zip_bytes(
            pdf_bytes=pdf_bytes,
            plan=plan,
            strict_pages=strict_pages,
        )

        st.success("Готово!")
        st.download_button(
            "Скачать ZIP",
            data=zip_bytes,
            file_name="split_files.zip",
            mime="application/zip",
        )

        st.code("\n".join(logs))

    except Exception as e:
        st.error(f"Ошибка: {e}")
