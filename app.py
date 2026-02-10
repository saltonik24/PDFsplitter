import io
from typing import List

import streamlit as st

from splitter import SplitPlan, split_pdf_to_zip_bytes


def read_names_from_txt(file_bytes: bytes) -> List[str]:
    text = file_bytes.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    return [x for x in lines if x]


def read_names_from_xlsx(file_bytes: bytes) -> List[str]:
    # pandas + openpyxl
    import pandas as pd

    df = pd.read_excel(io.BytesIO(file_bytes))
    if "filename" not in df.columns:
        raise ValueError("В Excel должна быть колонка с названием: filename")
    names = df["filename"].astype(str).tolist()
    names = [x.strip() for x in names if str(x).strip()]
    return names


st.set_page_config(page_title="PDF Splitter", page_icon="📄", layout="centered")

st.title("📄 Нарезка PDF на документы и выгрузка ZIP")

st.write(
    "Загрузи PDF и файл с именами (TXT или XLSX), укажи количество страниц на 1 документ."
)

pages_per_doc = st.number_input(
    "Количество страниц в одном документе",
    min_value=1,
    value=3,
    step=1,
)

strict_pages = st.checkbox(
    "Строгое совпадение количества страниц (PDF должен ровно совпадать с names * pages)",
    value=True,
)

pdf_file = st.file_uploader("Загрузи PDF", type=["pdf"])
names_file = st.file_uploader("Загрузи names.txt или names.xlsx", type=["txt", "xlsx"])

with st.expander("Шаблон names.txt / names.xlsx", expanded=False):
    st.markdown(
        """
**names.txt**: одна строка = одно имя файла (можно без .pdf)  
Пример:
