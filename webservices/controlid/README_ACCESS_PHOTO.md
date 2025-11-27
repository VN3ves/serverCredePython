# Sistema de Fotos de Acesso

## Visão Geral

O endpoint `/api/notifications/access_photo` recebe fotos enviadas pelos leitores faciais sempre que há um evento de identificação.

## Fluxo de Processamento

1. **Leitor facial** detecta um evento de acesso (identificado ou não)
2. **Leitor envia** requisição POST com a foto em base64
3. **Servidor processa**:
   - Decodifica a foto de base64 para bytes
   - Salva a foto como arquivo .jpg no disco
   - Registra na tabela `tblArquivo`
   - Relaciona com a entrada em `tblEntradas` (se existir)

## Estrutura de Diretórios

```
/midia/
├── pessoas/
│   └── {user_id}/
│       └── acessos/
│           └── acesso_YYYYMMDD_HHMMSS_ffffff.jpg
└── acessos/
    └── nao_identificados/
        └── acesso_YYYYMMDD_HHMMSS_ffffff.jpg
```

- **Usuário identificado**: `/midia/pessoas/{user_id}/acessos/`
- **Não identificado**: `/midia/acessos/nao_identificados/`

## Formato da Requisição

### Headers
```
Content-Type: application/x-www-form-urlencoded
ou
Content-Type: application/json
```

### Body (form-urlencoded)
```
device_id=478435
time=1532977090
portal_id=1
identifier_id=0
event=7
user_id=123
access_photo=<base64_encoded_jpeg>
```

### Body (JSON)
```json
{
  "device_id": "478435",
  "time": "1532977090",
  "portal_id": "1",
  "identifier_id": "0",
  "event": "7",
  "user_id": "123",
  "access_photo": "<base64_encoded_jpeg>"
}
```

## Tabelas do Banco de Dados

### tblArquivo
Armazena informações sobre o arquivo da foto:
- `id`: ID do arquivo
- `idEvento`: ID do evento
- `idReferencia`: ID da pessoa (ou leitor se não identificado)
- `tipoReferencia`: 'PESSOA' ou 'LEITOR'
- `tipoArquivo`: 'ACESSO'
- `pathLocal`: Caminho do arquivo no disco
- `dataCadastro`: Data de cadastro

### tblEntradas
Relaciona a foto com a tentativa de acesso:
- `idArquivo`: ID do arquivo de foto (FK para tblArquivo)
- Outros campos da entrada...

## Instalação

1. Execute o SQL de alterações:
```bash
mysql -u usuario -p banco < /var/www/server/webservices/controlid/sql/alteracoes_access_photo.sql
```

2. Certifique-se de que o diretório `/midia` tem permissões corretas:
```bash
sudo chown -R www-data:www-data /var/www/midia
sudo chmod -R 755 /var/www/midia
```

## Logs

Os logs são salvos em: `/var/www/logs/logAccessPhoto.log`

## Configuração no Leitor

Para habilitar o envio de fotos, configure o leitor:

```json
{
  "monitor": {
    "enable_photo_upload": "1"
  }
}
```

## Testando

### Teste Manual
```bash
curl -X POST http://seu-servidor:10080/api/notifications/access_photo \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "123",
    "user_id": "456",
    "event": "7",
    "portal_id": "1",
    "time": "1234567890",
    "identifier_id": "0",
    "access_photo": "/9j/4AAQSkZJRgABAQEA..."
  }'
```

### Verificar Logs
```bash
tail -f /var/www/logs/logAccessPhoto.log
```

## Troubleshooting

### Foto não é salva
- Verificar permissões do diretório `/midia`
- Verificar se o base64 está correto
- Verificar logs em `logAccessPhoto.log`

### Foto não relacionada com entrada
- A entrada deve existir antes da foto chegar
- Verificar se `user_id` e `leitor_id` estão corretos
- Pode haver delay entre entrada e foto

