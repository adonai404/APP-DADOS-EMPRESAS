# 🏢 Sistema Unificado de Dados Fiscais

Sistema automatizado para extrair e consolidar dados de documentos fiscais (ENTRADAS e PGDAS) com detecção automática de tipo de documento.

## 🚀 Funcionalidades

- **Detecção Automática**: Identifica automaticamente se o PDF é um relatório de Entradas ou documento PGDAS
- **Extração Inteligente**: Extrai dados importantes como CNPJ, empresa, período, valores fiscais
- **Consolidação**: Agrupa dados da mesma empresa e período automaticamente
- **Exportação Excel**: Gera planilha XLSX com dados consolidados incluindo coluna "Situação"
- **Interface Intuitiva**: Interface web responsiva e fácil de usar

## 📋 Dados Extraídos

### Relatórios de Entradas:
- Nome da Empresa
- CNPJ
- Período
- Total de Entradas

### Documentos PGDAS:
- Nome da Empresa
- CNPJ
- Período de Apuração
- RBT12 (Receita Bruta dos 12 meses)
- Receita Bruta Informada
- Total do Débito Declarado

## 🛠️ Como Usar

1. **Upload de Arquivos**: Faça upload dos PDFs (pode misturar ENTRADAS e PGDAS)
2. **Processamento Automático**: O sistema detecta e processa cada arquivo automaticamente
3. **Visualização**: Veja os dados consolidados na tabela
4. **Filtros**: Use os filtros para buscar empresas específicas ou tipos de dados
5. **Exportação**: Baixe a planilha Excel com todos os dados consolidados

## 🔧 Instalação Local

```bash
# Clone o repositório
git clone <seu-repositorio>

# Instale as dependências
pip install -r requirements.txt

# Execute o app
streamlit run app.py
```

## 📦 Deploy no Streamlit Cloud

1. Faça push do código para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte sua conta GitHub
4. Selecione o repositório e branch
5. O Streamlit Cloud fará o deploy automaticamente

## 📊 Estrutura da Planilha Exportada

| Coluna | Descrição |
|--------|-----------|
| Empresa | Nome da empresa |
| CNPJ | CNPJ da empresa |
| Período | Período de referência |
| RBT12 | Receita Bruta dos 12 meses |
| entrada | Total de entradas |
| saída | Receita bruta informada |
| imposto | Total do débito declarado |
| Situação | Coluna para preenchimento manual |

## ⚠️ Requisitos

- Python 3.8+
- Streamlit
- Pandas
- PDFplumber
- OpenPyXL

## 🐛 Solução de Problemas

- **Erro de upload**: Verifique se os arquivos são PDFs válidos
- **Dados não extraídos**: Confirme se o PDF contém as informações esperadas
- **Erro de processamento**: Verifique se o PDF não está corrompido

## 📝 Licença

Este projeto é de uso interno para processamento de dados fiscais.
