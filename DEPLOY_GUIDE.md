# 🚀 Guia de Deploy - Streamlit Cloud

## ✅ App Pronto para Deploy!

O app está completamente configurado e otimizado para deploy no Streamlit Cloud.

## 📁 Estrutura do Projeto

```
APP-DADOS-EMPRESAS/
├── app.py                    # Aplicação principal
├── requirements.txt          # Dependências Python
├── packages.txt             # Pacotes do sistema (se necessário)
├── README.md                # Documentação do projeto
├── .gitignore              # Arquivos ignorados pelo Git
└── .streamlit/
    └── config.toml         # Configurações do Streamlit
```

## 🛠️ Passos para Deploy

### 1. Preparar Repositório Git
```bash
# Inicializar repositório (se ainda não foi feito)
git init

# Adicionar todos os arquivos
git add .

# Fazer commit inicial
git commit -m "Initial commit: Sistema Unificado de Dados Fiscais"

# Conectar ao repositório remoto (substitua pela sua URL)
git remote add origin https://github.com/SEU_USUARIO/APP-DADOS-EMPRESAS.git

# Fazer push
git push -u origin main
```

### 2. Deploy no Streamlit Cloud

1. **Acesse**: [share.streamlit.io](https://share.streamlit.io)
2. **Login**: Conecte sua conta GitHub
3. **New App**: Clique em "New app"
4. **Configurações**:
   - **Repository**: Selecione seu repositório
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Escolha um nome único (ex: `dados-fiscais-app`)

5. **Deploy**: Clique em "Deploy!"

## ⚙️ Configurações Aplicadas

### Streamlit Config (`.streamlit/config.toml`)
- ✅ Modo headless habilitado
- ✅ CORS desabilitado para produção
- ✅ XSRF protection desabilitado
- ✅ Tema personalizado aplicado
- ✅ Estatísticas de uso desabilitadas

### Dependências (`requirements.txt`)
- ✅ Streamlit >= 1.28.0
- ✅ Pandas >= 2.0.0
- ✅ PDFplumber >= 0.9.0
- ✅ OpenPyXL >= 3.1.0

### Otimizações Implementadas
- ✅ Cache de dados com `@st.cache_data`
- ✅ Tratamento robusto de erros
- ✅ Logging configurado
- ✅ Limpeza automática de arquivos temporários
- ✅ Validação de colunas para evitar KeyError

## 🔧 Funcionalidades do App

- **Detecção Automática**: Identifica tipo de documento (ENTRADAS/PGDAS)
- **Extração de Dados**: CNPJ, empresa, período, valores fiscais
- **Consolidação**: Agrupa dados por empresa e período
- **Exportação Excel**: Planilha com coluna "Situação" incluída
- **Interface Responsiva**: Filtros, busca e ordenação

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
| **Situação** | **Coluna para preenchimento manual** |

## 🚨 Troubleshooting

### Erro de Dependências
- Verifique se `requirements.txt` está correto
- Adicione pacotes do sistema em `packages.txt` se necessário

### Erro de Memória
- O app usa cache para otimizar performance
- Arquivos temporários são limpos automaticamente

### Erro de Upload
- Verifique se os PDFs são válidos
- Confirme se contêm as informações esperadas

## 🎯 Próximos Passos

1. **Deploy**: Siga os passos acima
2. **Teste**: Teste com arquivos reais
3. **Monitoramento**: Acompanhe logs no Streamlit Cloud
4. **Atualizações**: Use Git para atualizar o app

## 📞 Suporte

- **Logs**: Acesse a aba "Logs" no Streamlit Cloud
- **Documentação**: Consulte README.md
- **Issues**: Use o sistema de issues do GitHub

---

**✅ Seu app está pronto para produção!** 🚀
