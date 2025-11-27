import sys
import requests
import time
import os
import fcntl
import signal
import base64
from threading import Thread
from contextlib import contextmanager
from db.funcoes import (
    findLeitores,
)
from db import conectarBancoEvento
from webservices.controlid.configurarLeitor import isSessionValid
from config import SISTEMA_GERENCIAMENTO
from logging_config import get_sincronizar_imagens_logger

# Obtém o logger configurado para este módulo
logging = get_sincronizar_imagens_logger()

# Timeout global para evitar que o script fique travado (em segundos)
TIMEOUT_GLOBAL = 160  # 2min 40seg (antes dos 3 minutos do cron)

def lerImagemBase64(pathLocal, pathNuvem=None):
    """
    Lê uma imagem do disco ou nuvem e retorna em base64.
    
    Args:
        pathLocal: Caminho local da imagem (ex: /midia/pessoas/5/imagens/avatar/...)
        pathNuvem: URL da nuvem (se disponível)
        
    Returns:
        str: Imagem em base64 ou None se não encontrada
    """
    try:
        # Se tem pathNuvem, retorna diretamente (já está em base64)
        if pathNuvem:
            return pathNuvem
        
        # Se tem pathLocal, lê do disco
        if pathLocal:
            # Monta o caminho completo
            caminho_completo = os.path.join(SISTEMA_GERENCIAMENTO, pathLocal.lstrip('/'))
            
            if not os.path.exists(caminho_completo):
                logging.error('Arquivo não encontrado: %s', caminho_completo)
                return None
            
            # Lê o arquivo e converte para base64
            with open(caminho_completo, 'rb') as f:
                imagem_bytes = f.read()
                imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
                return imagem_base64
        
        return None
        
    except Exception as e:
        logging.error('Erro ao ler imagem: %s', str(e))
        return None

class TimeoutError(Exception):
    """Exceção levantada quando o timeout é atingido"""
    pass

def timeout_handler(signum, frame):
    """Handler para o sinal de timeout"""
    raise TimeoutError("Timeout atingido na sincronização")

@contextmanager
def file_lock(lock_path, timeout=5):
    """
    Context manager para gerenciar o lock de arquivo com timeout.
    Garante que o lock será sempre liberado, mesmo em caso de erro.
    """
    lock_file = None
    try:
        lock_file = open(lock_path, 'w')
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        
        # Tenta adquirir o lock com timeout
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        logging.info('Lock adquirido com sucesso (PID: %s)', os.getpid())
        yield lock_file
        
    except IOError:
        logging.warning('Não foi possível adquirir o lock - outro processo já está executando')
        raise
    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                logging.info('Lock liberado com sucesso (PID: %s)', os.getpid())
            except Exception as e:
                logging.error('Erro ao liberar o lock: %s', str(e))

def sincronizarImagens():
    """
    Sincroniza imagens de todas as pessoas com credenciais ativas para todos os leitores.
    Executa uma única vez e retorna.
    """
    print("Sincronizando imagens")
    leitores = findLeitores()
    print(f"Leitores encontrados: {leitores}")
    if not leitores:
        logging.info('Nenhum leitor facial encontrado para sincronização')
        return
    
    threads = []
    for leitor in leitores:
        if leitor.get('status') == 'T' and leitor.get('configurado') == 'T':
            thread = Thread(target=sincronizarImagensLeitor, args=(leitor,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            logging.info('Thread de sincronização iniciada para o leitor %s', leitor['nomeLeitor'])
        else:
            print(f"Leitor {leitor['nomeLeitor']} ignorado (status={leitor.get('status')}, configurado={leitor.get('configurado')})")
            logging.info('Leitor %s ignorado (status=%s, configurado=%s)', 
                        leitor['nomeLeitor'], leitor.get('status'), leitor.get('configurado'))
            
    print(f"Threads iniciadas: {threads}")
    
    # Aguarda todas as threads completarem (com timeout de segurança)
    for thread in threads:
        thread.join(timeout=100)  # Timeout de 100 segundos por thread
        if thread.is_alive():
            logging.error('Thread de sincronização para um leitor não finalizou no tempo esperado')
    
    logging.info('Todas as threads de sincronização finalizadas.')

def sincronizarImagensLeitor(leitor, max_retries=3, retry_delay=5):
    """
    Sincroniza imagens de um leitor específico (execução única).
    """
    logging.info('Iniciando sincronização para o leitor %s', leitor['nomeLeitor'])
    
    for attempt in range(max_retries):
        try:
            # Verifica se a sessão é válida
            session = isSessionValid(leitor)
            if not session:
                logging.error('Sessão inválida para o leitor %s (tentativa %d/%d)', 
                            leitor['nomeLeitor'], attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return False
            
            # Atualiza a sessão no objeto leitor
            leitor['session'] = session
            
            # Busca pessoas com credenciais ativas que precisam sincronizar imagens
            conn = conectarBancoEvento()
            cursor = conn.cursor(dictionary=True)
            
            # Query para encontrar pessoas com credenciais ativas
            cursor.execute("""
                SELECT DISTINCT p.id, p.nome
                FROM tblPessoa p
                INNER JOIN tblCredencial c ON p.id = c.idPessoa
                WHERE c.status = 'T' AND p.status = 'T'
            """)
            pessoas = cursor.fetchall()
            
            if not pessoas:
                logging.info('Nenhuma pessoa com credencial ativa encontrada para o leitor %s', leitor['nomeLeitor'])
                cursor.close()
                conn.close()
                return True
            
            user_images = []
            
            for pessoa in pessoas:
                # Busca a imagem mais recente da pessoa que não foi sincronizada com este leitor
                cursor.execute("""
                    SELECT a.id, a.pathLocal, a.pathNuvem
                    FROM tblArquivo a
                    WHERE a.idReferencia = %s 
                    AND a.tipoReferencia = 'PESSOA'
                    AND a.tipoArquivo = 'AVATAR'
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tblLeitorFoto lf 
                        WHERE lf.idArquivo = a.id 
                        AND lf.idLeitor = %s 
                        AND lf.status = 1
                    )
                    ORDER BY a.dataCadastro DESC 
                    LIMIT 1
                """, (pessoa['id'], leitor['id']))
                
                arquivo = cursor.fetchone()
                
                if arquivo:
                    # Lê a imagem do disco e converte para base64
                    imagem_base64 = lerImagemBase64(arquivo['pathLocal'], arquivo['pathNuvem'])
                    
                    if not imagem_base64:
                        logging.warning('Imagem não encontrada para pessoa %s (arquivo %s)', pessoa['id'], arquivo['id'])
                        continue
                    
                    # Verifica se o usuário existe no leitor, se não, cria
                    try:
                        user_exists_response = requests.post(
                            f"http://{leitor['ip']}/load_objects.fcgi?session={session}",
                            json={
                                'object': 'users',
                                'where': [{'object': 'users', 'field': 'id', 'operator': '=', 'value': pessoa['id']}]
                            },
                            headers={'Content-Type': 'application/json'},
                            timeout=5
                        )
                        
                        if user_exists_response.status_code == 200:
                            users = user_exists_response.json().get('users', [])
                            if not users:
                                # Cria o usuário no leitor
                                create_user_response = requests.post(
                                    f"http://{leitor['ip']}/create_objects.fcgi?session={session}",
                                    json={
                                        'object': 'users',
                                        'values': [{
                                            'id': pessoa['id'], 
                                            'registration': str(pessoa['id']), 
                                            'name': pessoa['nome']
                                        }]
                                    },
                                    headers={'Content-Type': 'application/json'},
                                    timeout=5
                                )
                                
                                if create_user_response.status_code != 200:
                                    logging.error('Falha ao criar usuário %s no leitor %s: %s', 
                                                pessoa['id'], leitor['nomeLeitor'], create_user_response.text)
                                    continue
                                else:
                                    logging.info('Usuário %s criado no leitor %s', pessoa['nome'], leitor['nomeLeitor'])
                        
                        # Adiciona à lista para envio
                        user_images.append({
                            'user_id': pessoa['id'],
                            'timestamp': int(time.time()),
                            'image': imagem_base64,
                            'arquivo_id': arquivo['id']
                        })
                        
                    except requests.exceptions.RequestException as e:
                        logging.error('Erro ao verificar/criar usuário %s no leitor %s: %s', 
                                    pessoa['id'], leitor['nomeLeitor'], str(e))
                        continue
            
            cursor.close()
            conn.close()
            
            # Envia as imagens em lotes
            if user_images:
                logging.info('Enviando %d imagens para o leitor %s', len(user_images), leitor['nomeLeitor'])
                enviarImagensEmLotes(leitor, session, user_images)
            else:
                logging.info('Nenhuma imagem nova para sincronizar com o leitor %s', leitor['nomeLeitor'])
            
            # Sincronização concluída com sucesso
            logging.info('Sincronização concluída para o leitor %s', leitor['nomeLeitor'])
            return True
            
        except Exception as e:
            logging.error('Erro inesperado na sincronização do leitor %s (tentativa %d/%d): %s', 
                        leitor['nomeLeitor'], attempt + 1, max_retries, str(e))
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                logging.error('Falha na sincronização do leitor %s após %d tentativas', 
                            leitor['nomeLeitor'], max_retries)
                return False
    
    return False

def enviarImagensEmLotes(leitor, session, user_images, batch_size=2 * 1024 * 1024):
    """
    Envia imagens em lotes para não exceder o tamanho máximo da requisição.
    """
    current_batch = []
    current_size = 0
    
    for image_data in user_images:
        # Calcula o tamanho da imagem
        image_size = len(image_data['image'].encode('utf-8')) if image_data['image'] else 0
        
        # Se adicionar esta imagem ultrapassar o tamanho do lote, envia o lote atual
        if current_size + image_size > batch_size and current_batch:
            enviarLote(leitor, session, current_batch)
            current_batch = []
            current_size = 0
        
        current_batch.append(image_data)
        current_size += image_size
    
    # Envia o último lote se houver imagens restantes
    if current_batch:
        enviarLote(leitor, session, current_batch)

def enviarLote(leitor, session, batch, max_retries=3, retry_delay=5):
    """
    Envia um lote de imagens para o leitor facial.
    """
    conn = None
    cursor = None
    
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor()
        
        for attempt in range(max_retries):
            try:
                # Verifica se a sessão ainda é válida
                session_check = isSessionValid(leitor)
                if not session_check:
                    logging.error('Sessão inválida ao enviar lote para o leitor %s', leitor['nomeLeitor'])
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        break
                
                session = session_check
                
                # Prepara o payload para envio
                payload = {
                    'match': False,
                    'user_images': [
                        {
                            'user_id': img['user_id'],
                            'timestamp': img['timestamp'],
                            'image': img['image']
                        } 
                        for img in batch
                    ]
                }
                
                # Envia as imagens
                response = requests.post(
                    f"http://{leitor['ip']}/user_set_image_list.fcgi?session={session}",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=90
                )
                
                # Registra o resultado de cada imagem
                for image_data in batch:
                    sucesso = response.status_code == 200
                    
                    if sucesso:
                        mensagem = "Imagem sincronizada com sucesso"
                        status = 1
                    else:
                        mensagem = f"Falha ao sincronizar: {response.text[:200]}"
                        status = 0
                    
                    # Registra na tabela tblLeitorFoto
                    cursor.execute("""
                        INSERT INTO tblLeitorFoto (idEvento, idLeitor, idArquivo, status, mensagem, dataCadastro)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (
                        leitor['idEvento'],
                        leitor['id'],
                        image_data['arquivo_id'],
                        status,
                        mensagem
                    ))
                
                conn.commit()
                
                if response.status_code == 200:
                    logging.info('Lote de %d imagens enviado com sucesso para o leitor %s', 
                               len(batch), leitor['nomeLeitor'])
                    break
                else:
                    logging.error('Falha ao enviar lote para o leitor %s: %s', 
                                leitor['nomeLeitor'], response.text)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    
            except requests.exceptions.RequestException as e:
                logging.error('Erro de requisição ao enviar lote para o leitor %s (tentativa %d/%d): %s', 
                            leitor['nomeLeitor'], attempt + 1, max_retries, str(e))
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    # Registra falha para todas as imagens do lote
                    for image_data in batch:
                        cursor.execute("""
                            INSERT INTO tblLeitorFoto (idEvento, idLeitor, idArquivo, status, mensagem, dataCadastro)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, (
                            leitor['idEvento'],
                            leitor['id'],
                            image_data['arquivo_id'],
                            0,
                            f"Erro na requisição: {str(e)[:200]}"
                        ))
                    conn.commit()
                    
    except Exception as e:
        logging.error('Erro inesperado ao enviar lote para o leitor %s: %s', leitor['nomeLeitor'], str(e))
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Execução principal com lock e timeout para evitar travamentos
if __name__ == '__main__':
    lock_file_path = '/tmp/sincronizar_imagens.lock'
    
    try:
        # Configura o timeout global usando signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_GLOBAL)
        
        # Usa o context manager para garantir que o lock será liberado
        with file_lock(lock_file_path):
            logging.info('Iniciando sincronização de imagens (PID: %s)', os.getpid())
            inicio = time.time()
            
            sincronizarImagens()
            
            duracao = time.time() - inicio
            logging.info('Sincronização finalizada com sucesso em %.2f segundos', duracao)
            
            # Cancela o alarme se terminou antes do timeout
            signal.alarm(0)
            
    except IOError:
        logging.warning("Outro processo de sincronização já está em execução")
        print("Outro processo de sincronização já está em execução")
        sys.exit(1)
        
    except TimeoutError:
        logging.error("Sincronização abortada por timeout após %d segundos", TIMEOUT_GLOBAL)
        print(f"Sincronização abortada por timeout após {TIMEOUT_GLOBAL} segundos")
        sys.exit(2)
        
    except Exception as e:
        logging.error("Erro fatal durante a sincronização: %s", str(e), exc_info=True)
        print(f"Erro fatal durante a sincronização: {str(e)}")
        sys.exit(3)
        
    finally:
        # Garante que o alarme seja cancelado
        signal.alarm(0)
        logging.info('Processo de sincronização finalizado')
