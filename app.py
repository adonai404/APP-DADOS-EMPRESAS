import streamlit as st
import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
import openpyxl
from io import BytesIO
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Extração de Dados Fiscais",
    page_icon="🏢",
    layout="wide"
)

@st.cache_data
def limpar_valor_monetario(valor_str):
    """
    Converte valor monetário do formato brasileiro para numérico
    Ex: "1.099,85" -> 1099.85
    """
    if not valor_str or valor_str == "Não encontrado":
        return 0.0
    
    # Remove R$ e espaços
    valor_limpo = valor_str.replace('R$', '').replace(' ', '').strip()
    
    # Remove pontos (separador de milhar) e substitui vírgula por ponto (decimal)
    valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
    
    try:
        return float(valor_limpo)
    except:
        return 0.0

def normalizar_cnpj(cnpj):
    """
    Normaliza CNPJ removendo caracteres especiais e mantendo apenas números
    """
    if not cnpj or cnpj == "Não encontrado" or pd.isna(cnpj):
        return ""
    return re.sub(r'[^\d]', '', str(cnpj))

def normalizar_nome_empresa(nome):
    """
    Normaliza nome da empresa para comparação
    """
    if not nome:
        return ""
    return nome.upper().strip()

def consolidar_dados_empresa(dados_originais):
    """
    Consolida dados de ENTRADAS e PGDAS da mesma empresa e período
    Usa lógica melhorada baseada em agrupamento por empresa + período
    """
    # Converter para DataFrame para facilitar o agrupamento
    df = pd.DataFrame(dados_originais)
    
    # Normalizar nome da empresa (remove espaços extras, maiúsculas/minúsculas)
    df["Empresa_norm"] = df["Empresa"].str.strip().str.upper()
    
    # Criar chave de agrupamento apenas com Empresa + Período
    # Usar período de acordo com o tipo de documento
    df["periodo_consolidado"] = df.apply(lambda row: 
        row.get('Período', '') if row.get('Tipo_Documento') == 'ENTRADAS' 
        else row.get('Período de Apuração', ''), axis=1)
    
    df["chave"] = df["Empresa_norm"] + "_" + df["periodo_consolidado"]
    
    # Mapear campos originais para os novos nomes
    # Criar colunas com os novos nomes baseados nos campos originais
    # Verificar se as colunas existem antes de acessá-las
    df["entrada"] = df.get("Total de Entradas", None)
    df["saída"] = df.get("Receita Bruta Informada", None)
    df["imposto"] = df.get("Total do Débito Declarado", None)
    
    # Converter campos numéricos para float, tratando valores não numéricos
    def converter_para_float(serie):
        """Converte série para float, tratando valores não numéricos"""
        resultado = []
        for valor in serie:
            if pd.isna(valor) or valor == "Não encontrado" or valor is None:
                resultado.append(None)
            else:
                try:
                    # Se já é numérico, mantém
                    if isinstance(valor, (int, float)):
                        resultado.append(float(valor))
                    else:
                        # Se é string, tenta converter
                        resultado.append(limpar_valor_monetario(str(valor)))
                except:
                    resultado.append(None)
        return pd.Series(resultado)
    
    # Aplicar conversão para campos numéricos
    df["entrada"] = converter_para_float(df["entrada"])
    df["saída"] = converter_para_float(df["saída"])
    df["imposto"] = converter_para_float(df["imposto"])
    df["RBT12"] = converter_para_float(df.get("RBT12", None))
    
    # Consolida somando os valores numéricos
    df_final = df.groupby(["chave", "Empresa_norm", "periodo_consolidado"], as_index=False).agg({
        "CNPJ": lambda x: ', '.join(x.dropna().unique()) if x.dropna().any() else None,  # mantém todos CNPJs encontrados
        "entrada": lambda x: x.sum() if x.notna().any() else None,
        "RBT12": lambda x: x.sum() if x.notna().any() else None,
        "saída": lambda x: x.sum() if x.notna().any() else None,
        "imposto": lambda x: x.sum() if x.notna().any() else None
    })
    
    # Renomear colunas para o formato final
    df_final = df_final.rename(columns={
        "Empresa_norm": "Empresa",
        "periodo_consolidado": "Período"
    })
    
    # Remover a coluna "chave" antes de retornar
    df_final = df_final.drop(columns=["chave"])
    
    # Adicionar coluna Situação vazia
    df_final["Situação"] = ""
    
    # Definir ordem das colunas
    ordem_colunas = [
        "Empresa",
        "CNPJ", 
        "Período",
        "RBT12",
        "entrada",
        "saída",
        "imposto",
        "Situação"
    ]
    
    # Reordenar colunas
    df_final = df_final[ordem_colunas]
    
    # Converter de volta para lista de dicionários
    dados_consolidados = df_final.to_dict('records')
    
    # Ordenar por empresa e período
    dados_consolidados.sort(key=lambda x: (x['Empresa'], x['Período']))
    
    return dados_consolidados

def detectar_tipo_documento(pdf_file):
    """
    Detecta automaticamente o tipo de documento baseado no conteúdo do PDF
    Retorna: 'ENTRADAS', 'PGDAS' ou 'DESCONHECIDO'
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Palavras-chave para identificar ENTRADAS
        palavras_entradas = [
            "Total de Entradas",
            "Relatório de Entradas",
            "Entradas do Período"
        ]
        
        # Palavras-chave para identificar PGDAS
        palavras_pgdas = [
            "PGDAS",
            "Programa Gerador do DAS",
            "Período de Apuração (PA)",
            "Receita bruta acumulada nos doze meses anteriores ao PA",
            "Receita Bruta do PA (RPA) - Competência",
            "Total Geral da Empresa",
            "IRPJ",
            "CSLL",
            "COFINS",
            "PIS/Pasep",
            "INSS/CPP",
            "ICMS",
            "IPI"
        ]
        
        # Contar ocorrências de palavras-chave
        contador_entradas = sum(1 for palavra in palavras_entradas if palavra.lower() in text.lower())
        contador_pgdas = sum(1 for palavra in palavras_pgdas if palavra.lower() in text.lower())
        
        # Determinar tipo baseado no maior número de ocorrências
        if contador_entradas > contador_pgdas and contador_entradas > 0:
            return "ENTRADAS"
        elif contador_pgdas > contador_entradas and contador_pgdas > 0:
            return "PGDAS"
        else:
            # Se não conseguir detectar claramente, tentar padrões mais específicos
            if "Total de Entradas:" in text:
                return "ENTRADAS"
            elif "PGDAS" in text or "Programa Gerador do DAS" in text:
                return "PGDAS"
            else:
                return "DESCONHECIDO"
                
    except Exception as e:
        st.error(f"Erro ao detectar tipo do documento: {str(e)}")
        return "DESCONHECIDO"

def extrair_dados_entradas(pdf_file):
    """
    Extrai dados do PDF de relatórios de entradas
    """
    data = {
        "Empresa": None,
        "CNPJ": None,
        "Período": None,
        "Total de Entradas": None,
        "Tipo_Documento": "ENTRADAS"
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

def extrair_dados_pgdas(pdf_path):
    """
    Extrai dados do PDF do PGDAS
    """
    dados_por_arquivo = {
        'CNPJ': None,
        'Empresa': "Não encontrado",
        'Período de Apuração': "Não encontrado",
        'RBT12': "Não encontrado",
        'Receita Bruta Informada': "Não encontrado",
        'Total do Débito Declarado': "Não encontrado",
        'Tipo_Documento': "PGDAS"
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pagina_num, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if texto:
                    lines = texto.split('\n')
                    
                    # Buscar RBT12
                    if dados_por_arquivo['RBT12'] == "Não encontrado":
                        for i, line in enumerate(lines):
                            if 'Receita bruta acumulada nos doze meses anteriores ao PA' in line and i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                valor_match = re.search(r'([\d.,]+)', next_line)
                                if valor_match:
                                    dados_por_arquivo['RBT12'] = valor_match.group(1)
                                    break
                    
                    # Buscar Período de Apuração
                    if dados_por_arquivo['Período de Apuração'] == "Não encontrado":
                        pa_match = re.search(r'Período de Apuração \(PA\)[:\s]*(\d{2}/\d{4})', texto, re.IGNORECASE | re.MULTILINE)
                        if pa_match:
                            dados_por_arquivo['Período de Apuração'] = pa_match.group(1)
                    
                    # Buscar Receita Bruta Informada
                    if dados_por_arquivo['Receita Bruta Informada'] == "Não encontrado":
                        for line in lines:
                            if 'Receita Bruta do PA (RPA) - Competência' in line:
                                valor_match = re.search(r'([\d.,]+)', line)
                                if valor_match:
                                    dados_por_arquivo['Receita Bruta Informada'] = valor_match.group(1)
                                    break
                    
                    # Buscar nome da empresa
                    if dados_por_arquivo['Empresa'] == "Não encontrado":
                        nome_match = re.search(r'Nome Empresarial[:\s]*([^,\n]+)', texto, re.IGNORECASE)
                        if nome_match:
                            dados_por_arquivo['Empresa'] = nome_match.group(1).strip()
                    
                    # Buscar Total do Débito Declarado
                    if dados_por_arquivo['Total do Débito Declarado'] == "Não encontrado":
                        for i, line in enumerate(lines):
                            if 'Total Geral da Empresa' in line:
                                for j in range(i+1, min(i+5, len(lines))):
                                    current_line = lines[j]
                                    if 'IRPJ' in current_line and 'CSLL' in current_line and 'COFINS' in current_line and 'Total' in current_line:
                                        if j + 1 < len(lines):
                                            valores_line = lines[j + 1]
                                            valores_match = re.findall(r'([\d.,]+)', valores_line)
                                            if valores_match:
                                                dados_por_arquivo['Total do Débito Declarado'] = valores_match[-1]
                                                break
                                break
                        
                        if dados_por_arquivo['Total do Débito Declarado'] == "Não encontrado":
                            for i, line in enumerate(lines):
                                valores_match = re.findall(r'([\d.,]+)', line)
                                if len(valores_match) >= 8:
                                    if i > 0 and 'IRPJ' in lines[i-1] and 'CSLL' in lines[i-1] and 'COFINS' in lines[i-1]:
                                        dados_por_arquivo['Total do Débito Declarado'] = valores_match[-1]
                                        break
                        
                        if dados_por_arquivo['Total do Débito Declarado'] == "Não encontrado":
                            for i, line in enumerate(lines):
                                if 'Total do Débito Declarado' in line and '(exigível + suspenso)' in line:
                                    for j in range(i+1, min(i+4, len(lines))):
                                        valores_line = lines[j]
                                        valores_match = re.findall(r'([\d.,]+)', valores_line)
                                        if len(valores_match) >= 8:
                                            dados_por_arquivo['Total do Débito Declarado'] = valores_match[-1]
                                            break
                                    break
    
    except Exception as e:
        st.error(f"Erro ao processar o PDF: {str(e)}")
        return []
    
    return [dados_por_arquivo] if any(valor != "Não encontrado" for valor in dados_por_arquivo.values()) else []

def main():
    st.title("Extração de Dados Fiscais")
    st.markdown("---")
    
    
    # # Informações sobre detecção automática
    # st.info("🤖 **Detecção Automática**: O sistema reconhece automaticamente se o PDF é um relatório de Entradas ou documento PGDAS. Apenas faça upload dos arquivos!")
    
    # Upload único de arquivos
    st.subheader("📄 Upload de Arquivos")
    uploaded_files = st.file_uploader(
        "Selecione os arquivos PDFs",
        type="pdf",
        accept_multiple_files=True,
        help="Você pode misturar arquivos de Entradas e PGDAS. O sistema reconhecerá cada um automaticamente."
    )
    
    if uploaded_files:
        # Processar arquivos com detecção automática
        with st.spinner("Processando arquivos e detectando tipos automaticamente..."):
            todos_dados = []
            dados_por_empresa = {}
            tipos_detectados = {}
            
            # Barra de progresso
            progress_bar = st.progress(0)
            total_files = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Atualizar barra de progresso
                progress_bar.progress((i + 1) / total_files)
                
                try:
                    # Salvar arquivo temporariamente
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Detectar tipo do documento automaticamente
                    tipo_detectado = detectar_tipo_documento(temp_path)
                    tipos_detectados[uploaded_file.name] = tipo_detectado
                    
                    # Fallback para PGDAS se não identificado
                    if tipo_detectado == "DESCONHECIDO":
                        tipo_detectado = "PGDAS"
                    
                    # Processar baseado no tipo detectado
                    if tipo_detectado == "ENTRADAS":
                        dados = extrair_dados_entradas(temp_path)
                        if dados and dados["Empresa"]:
                            todos_dados.append(dados)
                            
                            # Agrupar por empresa
                            empresa = dados["Empresa"]
                            if empresa not in dados_por_empresa:
                                dados_por_empresa[empresa] = {
                                    'dados_empresa': {
                                        'CNPJ': dados.get('CNPJ', 'Não encontrado'),
                                        'Nome_Empresa': empresa
                                    },
                                    'entradas': [],
                                    'pgdas': []
                                }
                            dados_por_empresa[empresa]['entradas'].append(dados)
                    
                    elif tipo_detectado == "PGDAS":
                        dados = extrair_dados_pgdas(temp_path)
                        for dado in dados:
                            if dado and dado["Empresa"]:
                                todos_dados.append(dado)
                                
                                # Agrupar por empresa
                                empresa = dado["Empresa"]
                                if empresa not in dados_por_empresa:
                                    dados_por_empresa[empresa] = {
                                        'dados_empresa': {
                                            'CNPJ': dado.get('CNPJ', 'Não encontrado'),
                                            'Nome_Empresa': empresa
                                        },
                                        'entradas': [],
                                        'pgdas': []
                                    }
                                dados_por_empresa[empresa]['pgdas'].append(dado)
                    
                except Exception as e:
                    st.error(f"Erro ao processar arquivo {uploaded_file.name}: {str(e)}")
                    logger.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
                
                finally:
                    # Limpar arquivo temporário
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except:
                            pass
            
            # Limpar barra de progresso
            progress_bar.empty()
            
            # Mostrar resumo da detecção
            st.markdown("### 📊 Resumo da Detecção Automática")
            col1, col2, col3 = st.columns(3)
            
            entradas_count = sum(1 for tipo in tipos_detectados.values() if tipo == "ENTRADAS")
            pgdas_count = sum(1 for tipo in tipos_detectados.values() if tipo == "PGDAS")
            desconhecidos_count = sum(1 for tipo in tipos_detectados.values() if tipo == "DESCONHECIDO")
            
            with col1:
                st.metric("📊 Relatórios de Entradas", entradas_count)
            with col2:
                st.metric("📋 Documentos PGDAS", pgdas_count)
            with col3:
                st.metric("❓ Não Identificados", desconhecidos_count)
            
        if todos_dados:
            st.markdown("### 📊 Dados Extraídos")
            
            # Consolidar dados da mesma empresa e período
            dados_consolidados = consolidar_dados_empresa(todos_dados)
            
            # Criar DataFrame unificado
            df_unificado = pd.DataFrame(dados_consolidados)
            
            # Mostrar informações sobre consolidação
            st.info(f"🔄 **Consolidação Automática**: {len(todos_dados)} registros originais foram consolidados em {len(dados_consolidados)} registros únicos por empresa/período")
            
            # Filtros
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                busca_empresa = st.text_input("🔍 Buscar empresa:", placeholder="Digite o nome da empresa...")
            
            with col2:
                filtro_dados = st.selectbox("📄 Dados:", ["Todos", "Com Entradas", "Com PGDAS", "Completos"])
            
            with col3:
                ordenacao = st.selectbox("📊 Ordenar por:", ["Empresa", "Período", "Entrada", "Imposto"])
            
            # Aplicar filtros
            df_filtrado = df_unificado.copy()
            
            if busca_empresa:
                df_filtrado = df_filtrado[df_filtrado['Empresa'].str.contains(busca_empresa, case=False, na=False)]
            
            # Filtro por tipo de dados
            if filtro_dados == "Com Entradas":
                df_filtrado = df_filtrado[df_filtrado['entrada'].notna()]
            elif filtro_dados == "Com PGDAS":
                df_filtrado = df_filtrado[df_filtrado['RBT12'].notna()]
            elif filtro_dados == "Completos":
                df_filtrado = df_filtrado[
                    (df_filtrado['entrada'].notna()) & 
                    (df_filtrado['RBT12'].notna())
                ]
            
            # Ordenação
            if ordenacao == "Empresa":
                df_filtrado = df_filtrado.sort_values('Empresa')
            elif ordenacao == "Período":
                df_filtrado = df_filtrado.sort_values('Período')
            elif ordenacao == "Entrada":
                df_filtrado = df_filtrado.sort_values('entrada', ascending=False, na_last=True)
            elif ordenacao == "Imposto":
                df_filtrado = df_filtrado.sort_values('imposto', ascending=False, na_last=True)
            
            # Exibir tabela
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Estatísticas
            st.info(f"📈 Exibindo {len(df_filtrado)} de {len(df_unificado)} registros")
            
            
            # Download Excel
            st.markdown("### 📥 Exportação")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Planilha principal
                df_unificado.to_excel(writer, sheet_name='Dados Consolidados', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 Download Excel Completo",
                data=output.getvalue(),
                file_name=f"Dados_Consolidados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        else:
            st.warning("Nenhum dado foi encontrado nos PDFs. Verifique se os arquivos contêm as informações esperadas.")

if __name__ == "__main__":
    main()