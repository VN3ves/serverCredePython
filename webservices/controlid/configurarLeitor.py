import sys
import requests
import mysql.connector
import time
import logging
import os
import fcntl
from threading import Thread
from db.funcoes import (
    updateLeitorSession,
    updateLeitorDeviceId,  
    updateLeitorServerId,
    findLeitoresParaConfigurar,
    marcarLeitorConfigurado,
)

logging.basicConfig(
    filename='/var/www/logs/logConfigLeitor.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Função para fazer o login no leitor
def login(leitor):
    try:
        response = requests.post(
            f"http://{leitor['ip']}/login.fcgi",
            data={'login': leitor['usuario'], 'password': leitor['senha']},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        logging.error('Erro de conexão ao tentar logar no leitor %s: %s', leitor['nomeLeitor'], str(e))
        return None
    if response.status_code == 200:
        session = response.json().get('session')
        updateLeitorSession(leitor['id'], session)
        return session
    else:
        logging.error('Falha ao logar no leitor facial %s: %s', leitor['nomeLeitor'], response.text)
        return None

# Função para verificar se a sessão do leitor é válida
def isSessionValid(leitor):
    try:
        response = requests.get(f"http://{leitor['ip']}/session_is_valid.fcgi?session={leitor['session']}", timeout=5)
        if response.status_code == 200 and response.json().get('session_is_valid', False):
            return leitor['session']
        else:
            nova_session = login(leitor)
            if nova_session:
                logging.info('Sessão do leitor %s foi renovada com sucesso', leitor['nomeLeitor'])
                return nova_session
            else:
                logging.error('Falha ao renovar a sessão do leitor %s', leitor['nomeLeitor'])
                return None
    except requests.exceptions.RequestException:
        return None
    
def configurarLeitor(master_password="654123"):
    leitores = findLeitoresParaConfigurar()
    if not leitores:
        logging.info('Nenhum leitor facial encontrado para configuração')
        return
    
    for leitor in leitores:
        session = isSessionValid(leitor)
        if not session:
            logging.error('Sessão inválida para o leitor %s, tentando reconectar', leitor['nomeLeitor'])
            return False
        logging.info('Iniciando configuração do leitor %s', leitor['nomeLeitor'])
        try:
                device_response = requests.post(
                    f"http://{leitor['ip']}/load_objects.fcgi?session={session}",
                    json={
                        'object': 'devices',
                        'where': [{'object': 'devices', 'field': 'ip', 'operator': '=', 'value': leitor['ip']}]
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                if device_response.status_code == 200:
                    device_id = device_response.json().get('devices')[0].get('id')
                    updateLeitorDeviceId(leitor['id'], device_id)
                else:
                    logging.error('Falha ao obter o ID do dispositivo para o leitor %s: %s', leitor['nomeLeitor'], device_response.text)
                    return False
        except requests.exceptions.RequestException as e:
            logging.error('Erro ao obter o dispositivo para o leitor %s: %s', leitor['nomeLeitor'], str(e))
            return False
        server_url = leitor.get('serverUrl') + ":10080"
        update_or_create_server(leitor, session, server_url)
        changeMasterPassword(leitor, session, master_password)
        configure_monitor(leitor, session, server_url)
        configureRTSP(leitor, session)
        logging.info('Configuração do leitor %s concluída com sucesso', leitor['nomeLeitor'])
        marcarLeitorConfigurado(leitor['id'])
        return True
    
def configureRTSP(leitor, session):
    try:
        rtsp_response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
            json={
                'onvif': {
                    'rtsp_enabled': '1',
                    'rtsp_port': '10556',
                    'rtsp_username': 'CREDENCIAMENTO',
                    'rtsp_password': 'TIX1@CREDE',
                    'rtsp_flipped': '0',
                    'rtsp_codec': 'h264',
                    'rtsp_video_height' : '720',
                    'rtsp_video_width' : '1280',
                    'rtsp_rgb': '2',
                },
                'video_stream': {
                    'audio_enabled': '1',
                    'rtsp_watermark': '1',
                }
            },
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if rtsp_response.status_code == 200:
            logging.info('RTSP configurado com sucesso para o leitor %s', leitor['nomeLeitor'])
        else:
            logging.error('Falha ao configurar RTSP para o leitor %s: %s', leitor['nomeLeitor'], rtsp_response.text)
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao configurar RTSP para o leitor %s: %s', leitor['nomeLeitor'], str(e))
        return False
    return True

def changeMasterPassword(leitor, session, master_password):
    logging.info('Iniciando alteração da senha mestre para o leitor %s', leitor['nomeLeitor'])
    try:
        master_pass_response = requests.post(
            f"http://{leitor['ip']}/master_password.fcgi?session={session}",
            json={'password': master_password},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        logging.error('Falha ao alterar a senha mestre para o leitor %s: %s', leitor['nomeLeitor'], str(e))
        return False
    if master_pass_response.status_code == 200:
        logging.info('Senha mestre alterada com sucesso para o leitor %s', leitor['nomeLeitor'])
        return True
    else:
        logging.error('Falha ao alterar a senha mestre para o leitor %s: %s', leitor['nomeLeitor'], master_pass_response.text)
        return False

def update_or_create_server(leitor, session, server_url):
    logging.info('Atualizando ou criando servidor para o leitor %s', leitor['nomeLeitor'])
    try:
        exist_server_response = requests.post(
            f"http://{leitor['ip']}/load_objects.fcgi?session={session}",
            json={
                'object': 'devices',
                'where': [{'object': 'devices', 'field': 'id', 'operator': '=', 'server_id': int(leitor.get('serverId') or 0)}]
            },
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if exist_server_response.status_code == 200:
            update_response = requests.post(
                f"http://{leitor['ip']}/modify_objects.fcgi?session={session}",
                json={
                    'object': 'devices',
                    'values': {'ip': server_url},
                    'where': [{'object': 'devices', 'field': 'id', 'operator': '=', 'value': int(leitor['serverId'])}]
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if update_response.status_code != 200:
                logging.error('Falha ao atualizar o servidor: %s', update_response.text)
                return False
            else:
                configure_server(leitor, session, leitor['serverId'])
        else:
            create_response = requests.post(
                f"http://{leitor['ip']}/create_objects.fcgi?session={session}",
                json={
                    'object': 'devices',
                    'values': [{'name': 'Servidor do Credenciamento', 'ip': server_url, 'public_key': ''}]
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if create_response.status_code == 200:
                serverId = create_response.json().get('ids')[0]
                updateLeitorServerId(leitor['id'], serverId)
                configure_server(leitor, session, serverId)
            else:
                logging.error('Falha ao criar o servidor: %s', create_response.text)
                return False
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao atualizar ou criar o servidor para o leitor %s: %s', leitor['nomeLeitor'], str(e))
        return False
    return True

def configure_server(leitor, session, server_id):
    logging.info('Configurando servidor para o leitor %s', leitor['nomeLeitor'])
    try:
        config_response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
            json={'online_client': {'server_id': str(server_id)}},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if config_response.status_code == 200:
            online_response = requests.post(
                f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
                json={
                    'general': {
                        'online': '1', 
                        'local_identification': '0',
                        'auto_reboot_hour': '12',
                        'auto_reboot_minute': '0'
                        },
                    'online_client': {
                        'extract_template': '0', 
                        'max_request_attempts': '3',
                        'contingency_enabled': '0',
                        'request_timeout': '5000',
                        'alive_interval': '3000'
                        }
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if online_response.status_code == 200:
                logging.info('Configuração do servidor realizada com sucesso para o leitor %s', leitor['nomeLeitor'])
            else:
                logging.error('Falha ao ativar modo online para o leitor %s: %s', leitor['nomeLeitor'], online_response.text)
                return False
        else:
            logging.error('Falha ao configurar o servidor para o leitor %s: %s', leitor['nomeLeitor'], config_response.text)
            return False
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao configurar o servidor para o leitor %s: %s', leitor['nomeLeitor'], str(e))
        return False
    return True

def configure_monitor(leitor, session, server_url):
    logging.info('Configurando monitor para o leitor %s', leitor['nomeLeitor'])
    try:
        ip_sem_porta = server_url.split(':')[0]
        serverUrlString = str(ip_sem_porta)
        monitor_config = {
            "monitor": {
                "request_timeout": "5000",
                "hostname": serverUrlString,
                "port": "10080",
                "path": "api/notifications",
                "alive_interval": "60000"
            }
        }
        response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
            json=monitor_config,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if response.status_code == 200:
            logging.info('Monitor configurado com sucesso para o leitor %s', leitor['nomeLeitor'])
        else:
            logging.error('Falha ao configurar o monitor para o leitor %s: %s', leitor['nomeLeitor'], response.text)
            return
        photo_config = {
            "monitor": {"enable_photo_upload": "1"},
        }
        photo_response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
            json=photo_config,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if photo_response.status_code == 200:
            logging.info('Configuração de foto de acesso habilitada com sucesso para o leitor %s', leitor['nomeLeitor'])
        else:
            logging.error('Falha ao habilitar foto de acesso para o leitor %s: %s', leitor['nomeLeitor'], photo_response.text)
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao configurar o monitor para o leitor %s: %s', leitor['nomeLeitor'], str(e))