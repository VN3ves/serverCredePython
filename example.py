import sys
import requests
import mysql.connector
import time
import logging
import os
import fcntl
from threading import Thread

# Configuração do log
logging.basicConfig(
    filename='/var/www/html/event-management/public/logCompleto.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'crede',
    'password': '@crede2024',
    'database': 'event_management'
}

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def find_leitores():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM leitores_faciais")
    leitores = cursor.fetchall()
    cursor.close()
    conn.close()
    logging.info('Leitores faciais encontrados: %s', leitores)
    return leitores

def update_leitor_session(leitor_id, session):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE leitores_faciais SET session = %s WHERE id = %s", (session, leitor_id))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('Sessão atualizada para o leitor %d: %s', leitor_id, session)

def update_leitor_device_id(leitor_id, device_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE leitores_faciais SET device_id = %s WHERE id = %s", (device_id, leitor_id))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('ID do dispositivo atualizado para o leitor %d: %s', leitor_id, device_id)

def update_server_url_modified():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET modified = 1 WHERE `key` = 'server_url'")
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('Flag de modificação da URL do servidor atualizada')

def get_setting(key):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT value, modified FROM settings WHERE `key` = %s", (key,))
    setting = cursor.fetchone()
    cursor.close()
    conn.close()
    logging.info('Configuração obtida para %s: %s', key, setting)
    return setting

def change_master_password(leitor, master_password):
    logging.info('Iniciando alteração da senha mestre para o leitor %s', leitor['nome'])
    session = leitor['session']
    try:
        master_pass_response = requests.post(
            f"http://{leitor['ip']}/master_password.fcgi?session={session}",
            json={'password': master_password},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        logging.error('Falha ao alterar a senha mestre para o leitor %s: %s', leitor['nome'], str(e))
        return False
    if master_pass_response.status_code == 200:
        logging.info('Senha mestre alterada com sucesso para o leitor %s', leitor['nome'])
        return True
    else:
        logging.error('Falha ao alterar a senha mestre para o leitor %s: %s', leitor['nome'], master_pass_response.text)
        return False

def is_leitor_online(leitor_ip):
    try:
        response = requests.get(f"http://{leitor_ip}/session_is_valid.fcgi?session=0", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def login(leitor):
    logging.info('Iniciando login para o leitor %s', leitor['nome'])
    try:
        response = requests.post(
            f"http://{leitor['ip']}/login.fcgi",
            data={'login': leitor['usuario'], 'password': leitor['senha']},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        logging.error('Erro de conexão ao tentar logar no leitor %s: %s', leitor['nome'], str(e))
        return False
    if response.status_code == 200:
        session = response.json().get('session')
        update_leitor_session(leitor['id'], session)
        server_url = get_setting('server_url')
        master_password = get_setting('master_password')['value']
        if master_password and master_password['modified'] == 1:
            change_master_password(leitor, master_password)

        configure_monitor(leitor, session, server_url)
        if server_url and server_url['modified'] == 1:
            update_or_create_server(leitor, session, server_url)
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
                update_leitor_device_id(leitor['id'], device_id)
            else:
                logging.error('Falha ao obter o ID do dispositivo para o leitor %s: %s', leitor['nome'], device_response.text)
                return False
        except requests.exceptions.RequestException as e:
            logging.error('Erro ao obter o dispositivo para o leitor %s: %s', leitor['nome'], str(e))
            return False
        return True
    else:
        logging.error('Falha ao logar no leitor facial %s: %s', leitor['nome'], response.text)
        return False

def update_or_create_server(leitor, session, server_url):
    logging.info('Atualizando ou criando servidor para o leitor %s', leitor['nome'])
    try:
        exist_server_response = requests.post(
            f"http://{leitor['ip']}/load_objects.fcgi?session={session}",
            json={
                'object': 'devices',
                'where': [{'object': 'devices', 'field': 'id', 'operator': '=', 'server_id': int(leitor.get('server_id') or 0)}]
            },
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if exist_server_response.status_code == 200:
            update_response = requests.post(
                f"http://{leitor['ip']}/modify_objects.fcgi?session={session}",
                json={
                    'object': 'devices',
                    'values': {'ip': server_url['value']},
                    'where': [{'object': 'devices', 'field': 'id', 'operator': '=', 'value': int(leitor['server_id'])}]
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if update_response.status_code != 200:
                logging.error('Falha ao atualizar o servidor: %s', update_response.text)
                return False
            else:
                configure_server(leitor)
        else:
            create_response = requests.post(
                f"http://{leitor['ip']}/create_objects.fcgi?session={session}",
                json={
                    'object': 'devices',
                    'values': [{'name': 'Servidor de Credenciamento', 'ip': server_url['value'], 'public_key': ''}]
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if create_response.status_code == 200:
                server_id = create_response.json().get('ids')[0]
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE leitores_faciais SET server_id = %s WHERE id = %s", (str(server_id), leitor['id']))
                conn.commit()
                cursor.close()
                conn.close()
                configure_server(leitor)
            else:
                logging.error('Falha ao criar o servidor: %s', create_response.text)
                return False
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao atualizar ou criar o servidor para o leitor %s: %s', leitor['nome'], str(e))
        return False
    return True

def configure_server(leitor):
    logging.info('Configurando servidor para o leitor %s', leitor['nome'])
    try:
        config_response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={leitor['session']}",
            json={'online_client': {'server_id': str(leitor.get('server_id'))}},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if config_response.status_code == 200:
            online_response = requests.post(
                f"http://{leitor['ip']}/set_configuration.fcgi?session={leitor['session']}",
                json={
                    'general': {'online': '1', 'local_identification': '1'},
                    'online_client': {'extract_template': '0', 'max_request_attempts': '3'}
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if online_response.status_code == 200:
                logging.info('Configuração do servidor realizada com sucesso para o leitor %s', leitor['nome'])
            else:
                logging.error('Falha ao ativar modo online para o leitor %s: %s', leitor['nome'], online_response.text)
                return False
        else:
            logging.error('Falha ao configurar o servidor para o leitor %s: %s', leitor['nome'], config_response.text)
            return False
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao configurar o servidor para o leitor %s: %s', leitor['nome'], str(e))
        return False
    return True

def configure_monitor(leitor, session, server_url):
    logging.info('Configurando monitor para o leitor %s', leitor['nome'])
    try:
        monitor_config = {
            "monitor": {
                "request_timeout": "5000",
                "hostname": server_url['value'],
                "port": "80",
                "path": "api/notifications"
            }
        }
        response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
            json=monitor_config,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if response.status_code == 200:
            logging.info('Monitor configurado com sucesso para o leitor %s', leitor['nome'])
        else:
            logging.error('Falha ao configurar o monitor para o leitor %s: %s', leitor['nome'], response.text)
            return
        photo_config = {
            "monitor": {"enable_photo_upload": "1"}
        }
        photo_response = requests.post(
            f"http://{leitor['ip']}/set_configuration.fcgi?session={session}",
            json=photo_config,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if photo_response.status_code == 200:
            logging.info('Configuração de foto de acesso habilitada com sucesso para o leitor %s', leitor['nome'])
        else:
            logging.error('Falha ao habilitar foto de acesso para o leitor %s: %s', leitor['nome'], photo_response.text)
    except requests.exceptions.RequestException as e:
        logging.error('Erro ao configurar o monitor para o leitor %s: %s', leitor['nome'], str(e))

def sync_images(leitor, max_retries=3, retry_delay=5):
    while True:
        # if leitor['status'] == 0:
        #     logging.info('Leitor %s (ID: %d) está offline no banco, pulando sincronização', leitor['nome'], leitor['id'])
        #     time.sleep(20)
        #     continue
        for attempt in range(max_retries):
            try:
                logging.info('Tentativa %d de sincronização para o leitor %s', attempt + 1, leitor['nome'])
                if not is_leitor_online(leitor['ip']):
                    logging.warning('Leitor %s (ID: %d) está offline, tentativa %d', leitor['nome'], leitor['id'], attempt + 1)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        logging.error('Leitor %s (ID: %d) permaneceu offline após %d tentativas', leitor['nome'], leitor['id'], max_retries)
                        break
                session = leitor['session']
                server_url = get_setting('server_url')
                try:
                    session_valid_response = requests.get(
                        f"http://{leitor['ip']}/session_is_valid.fcgi?session={session}",
                        headers={'Content-Type': 'application/json'},
                        timeout=5
                    )
                except requests.exceptions.RequestException as e:
                    logging.error('Erro de sessão ao tentar sincronizar imagens no leitor %s: %s', leitor['nome'], str(e))
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    break
                if session_valid_response.status_code == 200 and not session_valid_response.json().get('session_is_valid'):
                    if not login(leitor):
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        break
                    logging.info('Sessão trocada')
                if server_url and server_url['modified'] == 1:
                    update_or_create_server(leitor, session, server_url)
                configure_monitor(leitor, session, server_url)
                conn = connect_db()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT funcionarios.* FROM funcionarios 
                    INNER JOIN credenciais ON funcionarios.id = credenciais.funcionario_id 
                    WHERE credenciais.ativo = 1 AND funcionarios.status = 1
                """)
                funcionarios = cursor.fetchall()
                user_images = []
                for funcionario in funcionarios:
                    cursor.execute("""
                        SELECT hf.* 
                            FROM historico_fotos hf
                            WHERE hf.funcionario_id = %s 
                            AND hf.tipo = 'cadastrada' 
                            AND NOT EXISTS (
                                SELECT 1 
                                FROM leitor_foto lf 
                                WHERE lf.foto_id = hf.id 
                                AND lf.leitor_id = %s 
                                AND lf.sucesso = 1
                            )
                            ORDER BY hf.created_at DESC 
                            LIMIT 1
                    """, (funcionario['id'], leitor['id']))
                    foto = cursor.fetchone()
                    if foto:
                        try:
                            user_exists_response = requests.post(
                                f"http://{leitor['ip']}/load_objects.fcgi?session={session}",
                                json={
                                    'object': 'users',
                                    'where': [{'object': 'users', 'field': 'id', 'operator': '=', 'value': funcionario['id']}]
                                },
                                headers={'Content-Type': 'application/json'},
                                timeout=5
                            )
                            if user_exists_response.status_code == 200 and not user_exists_response.json().get('users'):
                                create_user_response = requests.post(
                                    f"http://{leitor['ip']}/create_objects.fcgi?session={session}",
                                    json={
                                        'object': 'users',
                                        'values': [{'id': funcionario['id'], 'registration': str(funcionario['id']), 'name': funcionario['nome']}]
                                    },
                                    headers={'Content-Type': 'application/json'},
                                    timeout=5
                                )
                                if create_user_response.status_code != 200:
                                    logging.error('Falha ao criar o usuário %s no leitor facial: %s', funcionario['id'], create_user_response.text)
                                    continue
                            user_images.append({
                                'user_id': funcionario['id'],
                                'timestamp': int(time.time()),
                                'image': foto['foto'],
                                'foto_id': foto['id']
                            })
                        except requests.exceptions.RequestException as e:
                            logging.error('Erro ao verificar ou criar usuário para o funcionário %s: %s', funcionario['id'], str(e))
                            continue
                if user_images:
                    send_images_in_batches(leitor, leitor['ip'], session, user_images)
                cursor.close()
                conn.close()
                logging.info('Sincronização concluída com sucesso para o leitor %s', leitor['nome'])
                break
            except Exception as e:
                logging.error('Erro inesperado na sincronização do leitor %s (tentativa %d): %s', leitor['nome'], attempt + 1, str(e))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logging.error('Falha na sincronização do leitor %s após %d tentativas', leitor['nome'], max_retries)
                break
        time.sleep(20)

def send_images_in_batches(leitor, leitor_ip, session, user_images, batch_size=2 * 1024 * 1024):
    current_batch = []
    current_size = 0
    for image in user_images:
        image_size = len(image['image'].encode('utf-8'))
        if current_size + image_size > batch_size:
            send_batch(leitor_ip, session, current_batch, leitor)
            current_batch = []
            current_size = 0
        current_batch.append(image)
        current_size += image_size
    if current_batch:
        send_batch(leitor_ip, session, current_batch, leitor)

def send_batch(leitor_ip, session, batch, leitor, max_retries=3, retry_delay=5):
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        for attempt in range(max_retries):
            try:
                session_valid_response = requests.get(
                    f"http://{leitor['ip']}/session_is_valid.fcgi?session={session}",
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                if session_valid_response.status_code == 200 and not session_valid_response.json().get('session_is_valid'):
                    if not login(leitor):
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        break
                response = requests.post(
                    f"http://{leitor_ip}/user_set_image_list.fcgi?session={session}",
                    json={
                        'match': False,
                        'user_images': [{'user_id': image['user_id'], 'timestamp': image['timestamp'], 'image': image['image']} for image in batch]
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=90
                )
                for image in batch:
                    sucesso = response.status_code == 200
                    if sucesso:
                        mensagem = "Sincronização bem-sucedida!"
                        acao = "sincronizar"
                    else:
                        mensagem = f"Erro ao sincronizar imagem para o leitor {leitor['nome']}"
                        acao = "falha"
                    cursor.execute("""
                        INSERT INTO leitor_foto (leitor_id, foto_id, funcionario_id, sucesso, mensagem, dataCadastro, acao)
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """, (
                        leitor['id'],
                        image['foto_id'],
                        image['user_id'],
                        sucesso,
                        mensagem,
                        acao
                    ))
                conn.commit()
                if response.status_code == 200:
                    logging.info('Imagens sincronizadas com sucesso para o lote de %d imagens no leitor %s', len(batch), leitor['nome'])
                else:
                    logging.error('Falha ao enviar imagens para o leitor %s: %s', leitor['nome'], response.text)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                break
            except requests.exceptions.RequestException as e:
                logging.error('Erro ao enviar imagens para o leitor %s (tentativa %d): %s', leitor_ip, attempt + 1, str(e))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                for image in batch:
                    cursor.execute("""
                        INSERT INTO leitor_foto (leitor_id, foto_id, funcionario_id, sucesso, mensagem, dataCadastro, acao)
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """, (
                        leitor['id'],
                        image['foto_id'],
                        image['user_id'],
                        False,
                        f"Erro na requisição: {str(e)}",
                        "falha"
                    ))
                conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def sync_all():
    leitores = find_leitores()
    for leitor in leitores:
        thread = Thread(target=sync_images, args=(leitor,))
        thread.daemon = True
        thread.start()
    logging.info('Todas as threads de sincronização iniciadas.')

def main():
    sync_all()
    while True:
        time.sleep(3600)  # Mantém o programa rodando

lock_file = open('/tmp/sync_script.lock', 'w')
try:
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    main()
except IOError:
    print("Outro processo já está executando.")
finally:
    lock_file.close()