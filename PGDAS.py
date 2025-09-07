import streamlit as st
import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
import openpyxl
from io import BytesIO

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

def extrair_dados_pgdas(pdf_path):
    """
    Extrai dados do PDF do PGDAS incluindo RBT12, Período de Apuração, Receita Bruta, ISS e Total do Débito Declarado
    Retorna um único registro por arquivo PDF
    """
    dados_por_arquivo = {
        'CNPJ': "Não encontrado",
        'Empresa': "Não encontrado",
        'Período de Apuração': "Não encontrado",
        'RBT12': "Não encontrado",
        'Receita Bruta Informada': "Não encontrado",
        'ISS': "Não encontrado",
        'Total do Débito Declarado': "Não encontrado"
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pagina_num, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if texto:
                    lines = texto.split('\n')
                    
                    # Buscar RBT12 (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['RBT12'] == "Não encontrado":
                        for i, line in enumerate(lines):
                            if 'Receita bruta acumulada nos doze meses anteriores ao PA' in line and i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                valor_match = re.search(r'([\d.,]+)', next_line)
                                if valor_match:
                                    dados_por_arquivo['RBT12'] = valor_match.group(1)
                                    break
                    
                    # Buscar Período de Apuração (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['Período de Apuração'] == "Não encontrado":
                        pa_match = re.search(r'Período de Apuração \(PA\)[:\s]*(\d{2}/\d{4})', texto, re.IGNORECASE | re.MULTILINE)
                        if pa_match:
                            dados_por_arquivo['Período de Apuração'] = pa_match.group(1)
                    
                    # Buscar Receita Bruta Informada (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['Receita Bruta Informada'] == "Não encontrado":
                        for line in lines:
                            if 'Receita Bruta do PA (RPA) - Competência' in line:
                                valor_match = re.search(r'([\d.,]+)', line)
                                if valor_match:
                                    dados_por_arquivo['Receita Bruta Informada'] = valor_match.group(1)
                                    break
                    
                    # Buscar ISS (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['ISS'] == "Não encontrado":
                        for line in lines:
                            if 'ISS' in line and re.search(r'ISS\s+([\d.,]+)', line):
                                iss_match = re.search(r'ISS\s+([\d.,]+)', line)
                                if iss_match:
                                    dados_por_arquivo['ISS'] = iss_match.group(1)
                                    break
                    
                    # Buscar CNPJ (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['CNPJ'] == "Não encontrado":
                        cnpj_match = re.search(r'CNPJ Básico[:\s]*([\d.]+)', texto, re.IGNORECASE)
                        if cnpj_match:
                            dados_por_arquivo['CNPJ'] = cnpj_match.group(1)
                    
                    # Buscar nome da empresa (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['Empresa'] == "Não encontrado":
                        nome_match = re.search(r'Nome Empresarial[:\s]*([^,\n]+)', texto, re.IGNORECASE)
                        if nome_match:
                            dados_por_arquivo['Empresa'] = nome_match.group(1).strip()
                    
                    # Buscar Total do Débito Declarado (apenas se ainda não foi encontrado)
                    if dados_por_arquivo['Total do Débito Declarado'] == "Não encontrado":
                        # Buscar pela seção "Total Geral da Empresa"
                        for i, line in enumerate(lines):
                            if 'Total Geral da Empresa' in line:
                                # Procurar nas próximas linhas pela estrutura da tabela
                                for j in range(i+1, min(i+5, len(lines))):
                                    current_line = lines[j]
                                    
                                    # Verificar se é a linha com cabeçalhos dos impostos
                                    if 'IRPJ' in current_line and 'CSLL' in current_line and 'COFINS' in current_line and 'Total' in current_line:
                                        # A próxima linha deve conter os valores
                                        if j + 1 < len(lines):
                                            valores_line = lines[j + 1]
                                            # Extrair o último valor da linha (que é o total)
                                            # Procurar por padrão: números separados por espaços, terminando com o total
                                            valores_match = re.findall(r'([\d.,]+)', valores_line)
                                            if valores_match:
                                                # O último valor é o total
                                                dados_por_arquivo['Total do Débito Declarado'] = valores_match[-1]
                                                break
                                break
                        
                        # Busca alternativa: procurar diretamente pela linha com valores dos impostos
                        if dados_por_arquivo['Total do Débito Declarado'] == "Não encontrado":
                            for i, line in enumerate(lines):
                                # Procurar por linha que contenha valores monetários separados por espaços
                                # e que tenha pelo menos 8 valores (IRPJ, CSLL, COFINS, PIS/Pasep, INSS/CPP, ICMS, IPI, ISS, Total)
                                valores_match = re.findall(r'([\d.,]+)', line)
                                if len(valores_match) >= 8:
                                    # Verificar se a linha anterior contém os cabeçalhos dos impostos
                                    if i > 0 and 'IRPJ' in lines[i-1] and 'CSLL' in lines[i-1] and 'COFINS' in lines[i-1]:
                                        # O último valor é o total
                                        dados_por_arquivo['Total do Débito Declarado'] = valores_match[-1]
                                        break
                        
                        # Busca alternativa mais simples: procurar por linha com "Total do Débito Declarado"
                        if dados_por_arquivo['Total do Débito Declarado'] == "Não encontrado":
                            for i, line in enumerate(lines):
                                if 'Total do Débito Declarado' in line and '(exigível + suspenso)' in line:
                                    # Procurar nas próximas linhas pelos valores
                                    for j in range(i+1, min(i+4, len(lines))):
                                        valores_line = lines[j]
                                        valores_match = re.findall(r'([\d.,]+)', valores_line)
                                        if len(valores_match) >= 8:  # Pelo menos 8 valores (impostos + total)
                                            dados_por_arquivo['Total do Débito Declarado'] = valores_match[-1]
                                            break
                                    break
                    
                    # Não mostrar progresso detalhado por página para manter interface limpa
    
    except Exception as e:
        st.error(f"Erro ao processar o PDF: {str(e)}")
        return []
    
    # Retornar apenas um registro por arquivo
    return [dados_por_arquivo] if any(valor != "Não encontrado" for valor in dados_por_arquivo.values()) else []

def main():
    st.set_page_config(
        page_title="Extrator de Dados Fiscais",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Extrator de Dados Fiscais")
    st.markdown("---")
    
    
    # Upload múltiplo de arquivos
    uploaded_files = st.file_uploader(
        "Escolha os arquivos PDF do PGDAS (pode selecionar múltiplos)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Selecione um ou mais arquivos PDF do PGDAS para extrair os dados"
    )
    
    if uploaded_files:
        
        # Dicionário para agrupar dados por empresa
        dados_por_empresa = {}
        
        # Processar cada arquivo
        with st.spinner("Processando arquivos..."):
            for uploaded_file in uploaded_files:
                # Salvar arquivo temporariamente
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Extrair dados do PGDAS
                dados = extrair_dados_pgdas(temp_path)
                for dado in dados:
                    nome_empresa = dado.get('Empresa', 'Empresa Desconhecida')
                    
                    # Converter para formato de apuração
                    apuracao = {
                        'Periodo_Apuracao': dado.get('Período de Apuração', 'Não encontrado'),
                        'RBT12': dado.get('RBT12', 'Não encontrado'),
                        'Receita_Mes': dado.get('Receita Bruta Informada', 'Não encontrado'),
                        'Total_Debito': dado.get('Total do Débito Declarado', 'Não encontrado'),
                        'Arquivo': uploaded_file.name  # Adicionar arquivo à apuração
                    }
                    
                    if nome_empresa in dados_por_empresa:
                        # Verificar se já existe uma apuração com o mesmo período
                        periodo_existente = False
                        for ap_existente in dados_por_empresa[nome_empresa]['apuracoes']:
                            if ap_existente['Periodo_Apuracao'] == apuracao['Periodo_Apuracao']:
                                periodo_existente = True
                                break
                        
                        if not periodo_existente:
                            dados_por_empresa[nome_empresa]['apuracoes'].append(apuracao)
                    else:
                        dados_por_empresa[nome_empresa] = {
                            'dados_empresa': {
                                'CNPJ': dado.get('CNPJ', 'Não encontrado'),
                                'Nome_Empresa': nome_empresa,
                                'Data_Abertura': 'Não encontrado',
                                'Regime_Apuracao': 'Não encontrado',
                                'Optante_Simples': 'Não encontrado'
                            },
                            'apuracoes': [apuracao]
                        }
                
                # Limpar arquivo temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        if dados_por_empresa:
            st.markdown("### 📊 Dados Extraídos")
            
            # Criar lista com todos os dados de todas as empresas
            todos_dados = []
            for nome_empresa, dados_empresa in dados_por_empresa.items():
                for apuracao in dados_empresa['apuracoes']:
                    todos_dados.append({
                        'Empresa': nome_empresa,
                        'Período de Apuração': apuracao['Periodo_Apuracao'],
                        'RBT12': apuracao['RBT12'],
                        'Receita do Mês': apuracao['Receita_Mes'],
                        'imposto': apuracao['Total_Debito']
                    })
            
            # Criar DataFrame com todos os dados
            df_todos = pd.DataFrame(todos_dados)
            
            # Filtros e controles
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Busca por empresa
                busca_empresa = st.text_input("🔍 Buscar empresa:", placeholder="Digite o nome da empresa...")
            
            with col2:
                # Ordenação
                ordenacao = st.selectbox("📊 Ordenar por:", ["Empresa", "Período", "RBT12", "Receita", "Imposto"])
            
            with col3:
                # Limite de exibição
                limite_exibicao = st.selectbox("📄 Exibir:", ["Todas", "10", "25", "50", "100"])
            
            # Aplicar filtros
            df_filtrado = df_todos.copy()
            
            if busca_empresa:
                df_filtrado = df_filtrado[df_filtrado['Empresa'].str.contains(busca_empresa, case=False, na=False)]
            
            # Ordenação
            if ordenacao == "Empresa":
                df_filtrado = df_filtrado.sort_values('Empresa')
            elif ordenacao == "Período":
                df_filtrado = df_filtrado.sort_values('Período de Apuração')
            elif ordenacao == "RBT12":
                df_filtrado = df_filtrado.sort_values('RBT12', ascending=False)
            elif ordenacao == "Receita":
                df_filtrado = df_filtrado.sort_values('Receita do Mês', ascending=False)
            elif ordenacao == "Imposto":
                df_filtrado = df_filtrado.sort_values('imposto', ascending=False)
            
            # Limite de exibição
            if limite_exibicao != "Todas":
                df_filtrado = df_filtrado.head(int(limite_exibicao))
            
            # Exibir tabela principal
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Estatísticas do filtro
            st.info(f"📈 Exibindo {len(df_filtrado)} de {len(df_todos)} registros")
            
            # Resumo estatístico
            st.markdown("### 📈 Resumo Estatístico")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Empresas", len(dados_por_empresa))
            
            with col2:
                total_apuracoes = len(df_todos)
                st.metric("Total de Apurações", total_apuracoes)
            
            
            # Botão para download em Excel
            st.markdown("### 📥 Exportação")
            
            # Criar arquivo Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Planilha principal com todos os dados
                df_todos.to_excel(writer, sheet_name='Dados Consolidados', index=False)
                
                # Planilha de resumo por empresa
                resumo_empresas = []
                for nome_empresa, dados_empresa in dados_por_empresa.items():
                    total_rbt12 = sum(limpar_valor_monetario(ap['RBT12']) for ap in dados_empresa['apuracoes'])
                    total_receita = sum(limpar_valor_monetario(ap['Receita_Mes']) for ap in dados_empresa['apuracoes'])
                    total_debito = sum(limpar_valor_monetario(ap['Total_Debito']) for ap in dados_empresa['apuracoes'])
                    
                    resumo_empresas.append({
                        'Empresa': nome_empresa,
                        'CNPJ': dados_empresa['dados_empresa']['CNPJ'],
                        'Total Apurações': len(dados_empresa['apuracoes']),
                        'Total RBT12': total_rbt12,
                        'Total Receita': total_receita,
                        'Total Débito': total_debito
                    })
                
                df_resumo = pd.DataFrame(resumo_empresas)
                df_resumo.to_excel(writer, sheet_name='Resumo por Empresa', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 Download Excel (XLSX)",
                data=output.getvalue(),
                file_name=f"Dados_IMPORTAR{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        else:
            st.warning("Nenhum dado foi encontrado nos PDFs. Verifique se os arquivos contêm as informações esperadas.")
    
if __name__ == "__main__":
    main()
