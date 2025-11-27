from fastapi import FastAPI, HTTPException, Request, Response, Path
from fastapi.responses import JSONResponse
import httpx
import time
import os
from datetime import datetime
from config import SISTEMA_GERENCIAMENTO
from webservices.controlid.deviceAlive import handle_device_alive
from webservices.controlid.newAccess import handle_user_identified
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
    
@app.post("/new_biometric_image.fcgi")
@app.get("/new_biometric_image.fcgi")
async def new_biometric_template(request: Request):
    logging.info("Requisição em /new_biometric_template.fcgi")
    return JSONResponse(content={}, status_code=200)

@app.post("/new_user_identified.fcgi")
async def new_user_identified(request: Request):
    logging.info("Requisição em /new_user_identified.fcgi")
    try:
        data = await request.json()

        # response = handle_user_identified(
        #     device_id=data.get("device_id"),
        #     user_id=data.get("user_id"),
        #     event=data.get("event"),
        #     duress=data.get("duress"),
        #     face_mask=data.get("face_mask"),
        #     time=data.get("time"),
        #     portal_id=data.get("portal_id"),
        #     uuid=data.get("uuid"),
        #     block_read_data=data.get("block_read_data"),
        #     block_read_error=data.get("block_read_error"),
        #     card_value=data.get("card_value"),
        #     qrcode_value=data.get("qrcode_value"),
        #     uhf_tag=data.get("uhf_tag"),
        #     pin_value=data.get("pin_value"),
        #     user_has_image=data.get("user_has_image", False),
        #     user_name=data.get("user_name", ""),
        #     password=data.get("password", ""),
        #     confidence=data.get("confidence", 0.0),
        #     log_type_id=data.get("log_type_id", 1)
        # )
        logging.info(f"Dados recebidos em /new_user_identified.fcgi: {data}")
        return JSONResponse(content={
                'event': 6,
                'message': 'Fora do período de acesso.',
                'user_id': '0',
                'user_name': 'vitor',
                'user_image': False,
                'portal_id': '1'
                }, status_code=200)

    except Exception as e:
        logging.error(f"Erro ao processar /new_user_identified.fcgi: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar requisição")


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
    
