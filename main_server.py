from fastapi import FastAPI, HTTPException, Request, Response, Path
from fastapi.responses import JSONResponse
import httpx
import time
import os
import json
from urllib.parse import parse_qs
from datetime import datetime
from config import SISTEMA_GERENCIAMENTO
from webservices.controlid.deviceAlive import handle_device_alive
from webservices.controlid.newAccess import handle_user_identified
from webservices.controlid.accessPhoto import handle_access_photo
from logging_config import get_server_logger

app = FastAPI()

# Obtém o logger configurado para o servidor
logging = get_server_logger()

@app.post("/device_is_alive.fcgi")
async def device_is_alive(request: Request):
    logging.info("Requisição em /device_is_alive.fcgi")
    try:  
        dadosGet = request.query_params
        device_id = dadosGet.get('device_id')

        if not device_id:
            logging.error("device_id não fornecido em: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return JSONResponse(content={}, status_code=400)

        handle_device_alive(device_id)
        return JSONResponse(content={}, status_code=200)
        
    except Exception as e:
        logging.error(f"Erro ao processar /device_is_alive.fcgi: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar requisição")
    
@app.post("/api/notifications/access_photo")
async def access_photo(request: Request):
    logging.info("Requisição em /api/notifications/access_photo")
    try:
        # Obtém o body da requisição
        body = await request.body()
        
        if not body:
            logging.warning("Body vazio recebido em /api/notifications/access_photo")
            return JSONResponse(content={'message': 'Body vazio'}, status_code=400)
        
        # Parse do JSON
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao fazer parse do JSON: {str(e)}")
            return JSONResponse(content={'message': 'JSON inválido'}, status_code=400)
        
        logging.info(f"Foto de acesso recebida - device_id: {data.get('device_id')}, user_id: {data.get('user_id')}, event: {data.get('event')}")
        
        # Processa a foto de acesso
        result = handle_access_photo(
            device_id=data.get('device_id', '0'),
            time=data.get('time', ''),
            portal_id=data.get('portal_id', '0'),
            identifier_id=data.get('identifier_id', '0'),
            event=data.get('event', '0'),
            user_id=data.get('user_id', '0'),
            access_photo=data.get('access_photo', '')
        )
        
        if result['success']:
            return JSONResponse(content={'message': result['message']}, status_code=200)
        else:
            logging.error(f"Falha ao processar foto: {result['message']}")
            return JSONResponse(content={'message': result['message']}, status_code=200)  # Sempre 200 para não travar o leitor
            
    except Exception as e:
        logging.error(f"Erro ao processar /api/notifications/access_photo: {str(e)}", exc_info=True)
        return JSONResponse(content={'message': 'Erro interno'}, status_code=200)

@app.post("/new_user_identified.fcgi")
async def new_user_identified(request: Request):
    logging.info("Requisição em /new_user_identified.fcgi")
    try:
        # Verifica o Content-Type da requisição
        content_type = request.headers.get('content-type', '').lower()
        
        # Obtém o body da requisição
        body = await request.body()
        
        # Parse dos dados baseado no Content-Type
        data = {}
        if 'application/x-www-form-urlencoded' in content_type:
            # Parse manual de form-urlencoded usando urllib.parse
            body_str = body.decode('utf-8')
            parsed = parse_qs(body_str)
            # parse_qs retorna listas, pega o primeiro valor de cada chave
            data = {k: v[0] if isinstance(v, list) and len(v) > 0 else v for k, v in parsed.items()}
            logging.info(f"Dados recebidos como form-urlencoded em /new_user_identified.fcgi: {data}")
        else:
            logging.warning(f"Content-Type não suportado: {content_type}")
            return JSONResponse(content={}, status_code=400)
        
        if not data:
            logging.warning("Nenhum dado recebido em /new_user_identified.fcgi")
            return JSONResponse(content={}, status_code=400)
        
        response = handle_user_identified(
            device_id=data.get("device_id"),
            user_id=data.get("user_id"),
            event=data.get("event"),
            duress=data.get("duress"),
            face_mask=data.get("face_mask"),
            time=data.get("time"),
            portal_id=data.get("portal_id"),
            uuid=data.get("uuid"),
            block_read_data=data.get("block_read_data"),
            block_read_error=data.get("block_read_error"),
            card_value=data.get("card_value"),
            qrcode_value=data.get("qrcode_value"),
            uhf_tag=data.get("uhf_tag"),
            pin_value=data.get("pin_value"),
            user_has_image=data.get("user_has_image", False),
            user_name=data.get("user_name", ""),
            password=data.get("password", ""),
            confidence=data.get("confidence", 0.0),
            log_type_id=data.get("log_type_id", 1)
        )
        
        # Sempre retorna 200 pois o servidor processou corretamente
        # O leitor usa o campo 'event' da resposta para determinar acesso permitido/negado
        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        logging.error(f"Erro inesperado ao processar /new_user_identified.fcgi: {str(e)}", exc_info=True)
        # Mesmo em caso de erro, retorna 200 com event=1 (erro)
        return JSONResponse(content={
            'result': {
                'event': 1,
                'message': 'Erro interno do servidor.',
                'user_id': '0',
                'user_name': '',
                'user_image': False,
                'portal_id': '0'
            }
        }, status_code=200)


if __name__ == '__main__':
    import multiprocessing
    import uvicorn

    def start_http():
        uvicorn.run(app, host="0.0.0.0", port=10080)

    def start_https():
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=10443,
            ssl_keyfile="/etc/ssl/fastapi/fastapi.key",
            ssl_certfile="/etc/ssl/fastapi/fastapi.crt"
        )

    # Cria dois processos: HTTP e HTTPS
    p1 = multiprocessing.Process(target=start_http)
    p2 = multiprocessing.Process(target=start_https)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
    
