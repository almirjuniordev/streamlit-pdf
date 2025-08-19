# 📄 PDF Management System

Sistema de gerenciamento e processamento de PDFs com autenticação e interface administrativa.

## 🚀 Funcionalidades

### Para Usuários Básicos
- **Upload de PDFs**: Interface simples para envio de arquivos PDF
- **Processamento de PDFs**: Extração de metadados, texto e imagens
- **Download de Conteúdo**: Download do texto extraído e imagens
- **Interface Limpa**: Menu lateral simplificado com apenas upload de PDF

### Para Administradores
- **Gerenciamento de Usuários**: CRUD completo de usuários
- **Gerenciamento de Tipos de Usuário**: Criação e gestão de perfis
- **Acesso Total**: Todas as funcionalidades de usuário básico + admin

## 🔧 Tecnologias Utilizadas

- **Frontend**: Streamlit
- **Backend**: Python 3.9
- **Banco de Dados**: PostgreSQL
- **Processamento PDF**: PyPDF2, pdfplumber, PyMuPDF
- **Autenticação**: Argon2 (hash seguro)
- **Containerização**: Docker + Docker Compose

## 📋 Pré-requisitos

- Docker
- Docker Compose

## 🛠️ Instalação e Execução

### 1. Clone o repositório
```bash
git clone <repository-url>
cd streamlit-pdf
```

### 2. Execute o script de build
```bash
chmod +x build.sh
./build.sh
```

### 3. Acesse o sistema
Abra seu navegador e acesse: `http://localhost:8502`

## 👤 Usuários Padrão

### Administrador
- **Username**: admin
- **Password**: Admin@123
- **Tipo**: admin

### Usuário Básico
- **Username**: user
- **Password**: User@123
- **Tipo**: basic

## 📁 Estrutura do Projeto

```
streamlit-pdf/
├── streamlit_pdf_auth_ui/     # Módulo principal
│   ├── __init__.py           # Inicialização
│   ├── utils.py              # Utilitários e banco de dados
│   ├── widgets.py            # Interface de usuário
│   └── solution.py           # Funcionalidade de PDF
├── main.py                   # Ponto de entrada
├── config.yml                # Configuração de cookies
├── users_config.yml          # Usuários padrão
├── requirements.txt          # Dependências Python
├── Dockerfile                # Containerização
├── docker-compose.yml        # Orquestração
├── build.sh                  # Script de build
└── rebuild.sh                # Script de rebuild
```

## 🔐 Segurança

- **Hash de Senhas**: Argon2 para criptografia segura
- **Sessões**: Cookies com expiração de 30 dias
- **Validação**: Verificação de entrada e unicidade de dados
- **Autorização**: Controle de acesso baseado em tipos de usuário

## 📊 Funcionalidades de PDF

### Extração de Metadados
- Número de páginas
- Informações de criação
- Propriedades do documento

### Extração de Texto
- Texto completo do PDF
- Preview das primeiras 500 caracteres
- Download do texto em formato .txt

### Extração de Imagens
- Identificação de imagens por página
- Visualização das imagens extraídas
- Download individual das imagens

### Download
- Download do arquivo PDF original
- Download do texto extraído
- Download das imagens extraídas

## 🐳 Comandos Docker

### Construir e iniciar
```bash
./build.sh
```

### Reconstruir completamente
```bash
./rebuild.sh
```

### Parar serviços
```bash
docker-compose down
```

### Ver logs
```bash
docker-compose logs -f app
```

## 🔧 Configuração

### Variáveis de Ambiente
- `POSTGRES_HOST`: Host do banco de dados (padrão: postgres)
- `POSTGRES_USER`: Usuário do banco (padrão: postgres)
- `POSTGRES_PASSWORD`: Senha do banco (padrão: postgres)
- `POSTGRES_DB`: Nome do banco (padrão: auth_db)

### Portas
- **Aplicação**: 8502 (externa) -> 8502 (interna)
- **Banco de Dados**: 5433 (externa) -> 5432 (interna)

## 🧹 Limpeza Automática

O sistema possui limpeza automática de arquivos temporários:
- **Agendamento**: Diariamente à meia-noite
- **Pasta**: `uploaded_pdfs/`
- **Thread**: Execução em background

## 🐛 Solução de Problemas

### Erro de conexão com banco
```bash
docker-compose logs postgres
```

### Erro na aplicação
```bash
docker-compose logs app
```

### Reconstruir completamente
```bash
./rebuild.sh
```

## 📝 Licença

Este projeto está sob licença MIT.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
