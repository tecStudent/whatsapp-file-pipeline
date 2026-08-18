# WhatsApp File Pipeline

Pipeline orientado a eventos para **capturar automaticamente arquivos enviados em grupos do WhatsApp e armazená-los em um serviço de armazenamento em nuvem**, inicialmente utilizando o Google Drive.

O projeto tem como objetivo criar uma solução de baixo custo para centralizar e organizar documentos compartilhados pelo WhatsApp, evitando downloads e uploads manuais.

## 🎯 Objetivo

Automatizar o seguinte fluxo:

```text
WhatsApp Group
      │
      │ Arquivo enviado
      ▼
WhatsApp API
      │
      │ Webhook
      ▼
Python API
      │
      ├── Validação
      ├── Download
      └── Metadados
      │
      ▼
Storage
      │
      └── Google Drive
```

Quando um arquivo for enviado ao grupo monitorado, a aplicação deverá:

1. Receber o evento através de um webhook.
2. Identificar se a mensagem contém um arquivo.
3. Obter os metadados da mensagem.
4. Baixar o arquivo.
5. Validar o arquivo recebido.
6. Enviar o arquivo para o armazenamento configurado.
7. Registrar informações sobre o processamento.

## 🏗️ Arquitetura

A arquitetura inicial será composta por:

* **WhatsApp API** — origem das mensagens e arquivos.
* **Webhook** — recebe os eventos enviados pelo WhatsApp.
* **Python** — processamento principal da aplicação.
* **FastAPI** — exposição dos endpoints e recebimento dos webhooks.
* **Google Drive API** — armazenamento inicial dos arquivos.
* **Docker** — padronização do ambiente da aplicação.
* **Terraform** — provisionamento da infraestrutura cloud.

A arquitetura foi pensada para permitir futuramente outros destinos de armazenamento, como:

* Google Cloud Storage
* AWS S3
* OCI Object Storage
* Azure Blob Storage

## 📁 Estrutura do projeto

```text
whatsapp-file-pipeline/
│
├── src/
│   ├── api/
│   │   └── __init__.py
│   │
│   ├── ingestion/
│   │   └── __init__.py
│   │
│   ├── storage/
│   │   └── __init__.py
│   │
│   ├── metadata/
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── tests/
├── terraform/
├── docker/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### `src/api`

Responsável pelos endpoints HTTP da aplicação, incluindo o webhook utilizado para receber eventos do WhatsApp.

### `src/ingestion`

Responsável pela ingestão das mensagens e arquivos recebidos.

Entre suas responsabilidades estarão:

* identificar mensagens contendo arquivos;
* obter informações do arquivo;
* realizar o download;
* validar o conteúdo recebido.

### `src/storage`

Camada responsável pelo armazenamento.

A primeira implementação utilizará o **Google Drive**, mas a separação dessa camada permitirá adicionar outros provedores futuramente.

### `src/metadata`

Responsável pelo tratamento e persistência dos metadados associados aos arquivos.

Exemplos:

```text
file_name
file_type
sender
group
message_id
received_at
storage_path
processing_status
```

### `tests`

Testes unitários e de integração da aplicação.

### `terraform`

Código de Infrastructure as Code (IaC) utilizado para provisionar os recursos necessários para executar a aplicação.

### `docker`

Arquivos relacionados à criação e configuração dos containers da aplicação.

## 🔄 Fluxo de processamento

Exemplo:

```text
Usuário envia:

relatorio_agosto.xlsx

        ↓

WhatsApp gera evento

        ↓

Webhook recebe mensagem

        ↓

Aplicação identifica arquivo

        ↓

Arquivo é baixado

        ↓

Metadados são extraídos

        ↓

Arquivo é enviado ao Google Drive

        ↓

Processamento é registrado
```

No armazenamento, os arquivos poderão ser organizados automaticamente por data:

```text
WhatsApp Files/
│
└── 2026/
    ├── 08/
    │   ├── relatorio_agosto.xlsx
    │   └── documento.pdf
    │
    └── 09/
        └── relatorio_setembro.xlsx
```

## 🔐 Segurança

Credenciais e tokens **não devem ser versionados no GitHub**.

Variáveis sensíveis deverão ser fornecidas através de variáveis de ambiente.

Exemplo:

```env
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

GOOGLE_DRIVE_FOLDER_ID=
GOOGLE_CREDENTIALS_FILE=
```

O arquivo real `.env` deverá permanecer no `.gitignore`.

O repositório disponibilizará apenas:

```text
.env.example
```

sem valores sensíveis.

## 🐳 Docker

A aplicação será preparada para execução através de Docker.

A execução deverá futuramente ser possível com:

```bash
docker compose up --build
```

E para encerrar:

```bash
docker compose down
```

## 🧪 Testes

Os testes ficarão no diretório:

```text
tests/
```

E poderão ser executados com:

```bash
pytest
```

## 🗺️ Roadmap

* [ ] Criar estrutura inicial do projeto
* [ ] Configurar ambiente Python
* [ ] Criar API com FastAPI
* [ ] Criar endpoint de health check
* [ ] Implementar webhook
* [ ] Configurar integração com WhatsApp
* [ ] Identificar mensagens contendo arquivos
* [ ] Implementar download dos arquivos
* [ ] Integrar com Google Drive API
* [ ] Registrar metadados dos arquivos
* [ ] Implementar tratamento de erros e logs
* [ ] Criar testes unitários
* [ ] Containerizar aplicação com Docker
* [ ] Provisionar infraestrutura com Terraform
* [ ] Realizar deploy em ambiente cloud
* [ ] Configurar CI/CD com GitHub Actions

## 🚀 Status do projeto

> 🏗️ **Em desenvolvimento**

Atualmente o projeto encontra-se na fase inicial de definição da arquitetura e implementação da estrutura base.

## 💡 Possíveis evoluções

A arquitetura poderá ser expandida futuramente para suportar:

* múltiplos grupos;
* múltiplos destinos de armazenamento;
* organização automática por grupo/data;
* prevenção de arquivos duplicados;
* classificação automática de documentos;
* banco de metadados;
* dashboard de arquivos processados;
* notificações de falha;
* observabilidade;
* processamento assíncrono;
* integração com outros serviços de mensageria.

## 🛠️ Tecnologias

**Backend**

* Python
* FastAPI

**Integrações**

* WhatsApp API
* Google Drive API

**Infraestrutura**

* Docker
* Terraform

**Cloud Storage**

* Google Drive

**CI/CD**

* GitHub Actions

---

Este projeto foi desenvolvido com foco em **automação, integração entre APIs, arquitetura orientada a eventos e práticas de engenharia de software e dados**.
