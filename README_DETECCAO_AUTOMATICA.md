# 🤖 Sistema de Detecção Automática de Documentos

## 📋 Funcionalidades Implementadas

### ✅ **Detecção Automática de Tipo de Documento**
O sistema agora reconhece automaticamente se um PDF é:
- **📊 Relatório de Entradas** 
- **📋 Documento PGDAS**

### 🔍 **Como Funciona a Detecção**

#### **Para Relatórios de Entradas:**
O sistema busca por estas palavras-chave:
- "Total de Entradas"
- "Relatório de Entradas" 
- "Entradas do Período"

#### **Para Documentos PGDAS:**
O sistema busca por estas palavras-chave:
- "PGDAS"
- "Programa Gerador do DAS"
- "Período de Apuração (PA)"
- "Receita bruta acumulada nos doze meses anteriores ao PA"
- "Receita Bruta do PA (RPA) - Competência"
- "Total Geral da Empresa"
- "IRPJ", "CSLL", "COFINS", "PIS/Pasep", "INSS/CPP", "ICMS", "IPI", "ISS"

### 🚀 **Vantagens da Detecção Automática**

1. **✅ Simplicidade**: Não precisa especificar o tipo de documento
2. **🔄 Flexibilidade**: Pode misturar arquivos de diferentes tipos
3. **⚡ Eficiência**: Processamento mais rápido e direto
4. **🎯 Precisão**: Menos erros de classificação manual
5. **📊 Transparência**: Mostra exatamente o que foi detectado

### 📱 **Interface Atualizada**

- **Upload Único**: Um único campo para todos os PDFs
- **Feedback Visual**: Mostra o resultado da detecção para cada arquivo
- **Barra de Progresso**: Acompanha o processamento em tempo real
- **Resumo Estatístico**: Conta quantos de cada tipo foram detectados
- **Sidebar Informativa**: Explica como funciona a detecção

### 🔧 **Como Usar**

1. **Execute** `run_unificado.bat`
2. **Faça upload** de todos os PDFs (pode misturar tipos)
3. **Aguarde** a detecção automática
4. **Visualize** os resultados e análises
5. **Baixe** o relatório Excel completo

### 📊 **Exemplo de Uso**

```
📁 Pasta com arquivos:
├── empresa1_entradas_jan2024.pdf    → ✅ Detectado como ENTRADAS
├── empresa1_pgdas_jan2024.pdf       → ✅ Detectado como PGDAS  
├── empresa2_entradas_fev2024.pdf    → ✅ Detectado como ENTRADAS
└── empresa2_pgdas_fev2024.pdf       → ✅ Detectado como PGDAS

🎯 Resultado: Sistema processa todos automaticamente e gera análise comparativa!
```

### 🛡️ **Tratamento de Erros**

- **Arquivos não identificados**: Tentam processar como PGDAS (fallback)
- **Erros de leitura**: Mostram mensagem de erro específica
- **PDFs corrompidos**: São ignorados com aviso

### 📈 **Métricas de Detecção**

O sistema mostra:
- Quantos arquivos foram detectados como Entradas
- Quantos arquivos foram detectados como PGDAS  
- Quantos arquivos não foram identificados
- Taxa de sucesso da detecção

---

**🎉 Agora você pode simplesmente fazer upload de todos os seus PDFs e deixar o sistema fazer o trabalho de classificação automaticamente!**
