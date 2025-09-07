import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Relatório de Entradas", layout="wide")

st.title("📊 Relatório de Entradas - Empresas")

uploaded_files = st.file_uploader(
    "Selecione os relatórios em PDF",
    type="pdf",
    accept_multiple_files=True
)

def extract_data_from_pdf(pdf_file):
    data = {
        "Empresa": None,
        "CNPJ": None,
        "Período": None,
        "Total de Entradas": None,
    }

    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # Extrair nome da empresa
    empresa_match = re.search(r"([A-Z\s&]+LTDA)", text)
    if empresa_match:
        data["Empresa"] = empresa_match.group(1).strip()

    # Extrair CNPJ
    cnpj_match = re.search(r"CNPJ:\s*([\d./-]+)", text)
    if cnpj_match:
        data["CNPJ"] = cnpj_match.group(1).strip()

    # Extrair período e simplificar para MM/AAAA
    periodo_match = re.search(r"Período:\s*([\d/]+ até [\d/]+)", text)
    if periodo_match:
        periodo_completo = periodo_match.group(1).strip()
        # Extrair apenas o mês e ano do período
        mes_ano_match = re.search(r"(\d{2})/(\d{4})", periodo_completo)
        if mes_ano_match:
            data["Período"] = f"{mes_ano_match.group(1)}/{mes_ano_match.group(2)}"

    # Extrair apenas o total de entradas
    entradas_match = re.search(r"Total de Entradas:\s*([\d.,]+)", text)
    if entradas_match:
        data["Total de Entradas"] = float(entradas_match.group(1).replace(".", "").replace(",", "."))

    return data


if uploaded_files:
    results = []
    for pdf_file in uploaded_files:
        extracted = extract_data_from_pdf(pdf_file)
        results.append(extracted)

    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

    # Download Excel
    excel_file = "resultado_empresas.xlsx"
    df.to_excel(excel_file, index=False)

    with open(excel_file, "rb") as f:
        st.download_button("📥 Baixar Excel", f, file_name=excel_file)
