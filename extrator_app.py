import streamlit as st
import pdfplumber
import pandas as pd
import re
import warnings
import io

# Ocultar warnings irrelevantes
warnings.filterwarnings("ignore")

# Regex para extrair a tabela
padrao = re.compile(r"(\d+)\s+(\d{3}-\d\s*/\s*\d{5}-?\d*)\s+(.+?)\s+([\d.]+,\d{2})$")

# Configuração da página
st.set_page_config(page_title="Extrator de PDF para Excel", layout="wide")
st.title("📄 Extrator de Extrato Bancário (PDF → Excel)")

# Upload de múltiplos PDFs
arquivos_pdf = st.file_uploader(
    "Faça upload dos PDFs do extrato bancário", type="pdf", accept_multiple_files=True
)

if arquivos_pdf:
    dados_geral = []

    for arquivo in arquivos_pdf:
        dados = []
        periodo_listagem = None

        with pdfplumber.open(arquivo) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    linhas = texto.split("\n")

                    for linha in linhas:
                        linha = linha.strip()

                        # Extrair a linha com o período
                        if linha.startswith("A partir de:") and periodo_listagem is None:
                            periodo_listagem = linha.replace("A partir de:", "").strip()
                            continue

                        # Extrair linha da tabela com regex
                        match = padrao.search(linha)
                        if match:
                            numero_pagamento = match.group(1)
                            agencia_conta = match.group(2)
                            favorecido = match.group(3)
                            valor = match.group(4)
                            dados.append([numero_pagamento, agencia_conta, favorecido, valor])

        if dados:
            colunas = ["Número do Pagamento", "Agência/Conta", "Favorecido", "Valor (R$)"]
            df = pd.DataFrame(dados, columns=colunas)

            # Adiciona as novas colunas de data
            if periodo_listagem:
                df["Período da Listagem"] = periodo_listagem
                df["Data do Pagamento"] = periodo_listagem[-10:]
            else:
                df["Período da Listagem"] = "Não encontrado"
                df["Data do Pagamento"] = "Não encontrado"

            # Nome do arquivo como referência
            df["Arquivo"] = arquivo.name

            # Converte valores para float
            df["Valor (R$)"] = (
                df["Valor (R$)"]
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .astype(float)
            )

            dados_geral.append(df)

    if dados_geral:
        df_final = pd.concat(dados_geral, ignore_index=True)
        st.success("✅ Dados extraídos e consolidados com sucesso!")
        st.dataframe(df_final)

        # Gerar Excel na memória
        buffer = io.BytesIO()
        df_final.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Baixar Excel Consolidado",
            data=buffer,
            file_name="extrato_consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Nenhum dado foi extraído dos PDFs enviados.")
