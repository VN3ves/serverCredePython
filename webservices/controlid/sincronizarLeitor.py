#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronização forçada de imagens para um leitor específico.
Ignora histórico anterior e força nova sincronização de todas as pessoas com credenciais ativas.

Uso:
    python sincronizarLeitor.py <id_leitor>
    
Exemplo:
    python sincronizarLeitor.py 5
"""

import sys
import os

# Adiciona o diretório raiz do servidor ao path para permitir importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
import time
import base64
from db import conectarBancoEvento
from webservices.controlid.configurarLeitor import isSessionValid, login
from config import SISTEMA_GERENCIAMENTO
from logging_config import get_logger

# Obtém o logger configurado para este módulo
logging = get_logger('SincronizarLeitor', arquivo_log='logSincronizarLeitor.log')

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

def buscarLeitor(leitor_id):
    """
    Busca informações de um leitor específico pelo ID.
    
    Args:
        leitor_id: ID do leitor
        
    Returns:
        dict: Dados do leitor ou None se não encontrado
    """
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM tblLeitor 
            WHERE id = %s
            LIMIT 1
        """, (leitor_id,))
        
        leitor = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if leitor:
            logging.info('Leitor encontrado: %s (IP: %s)', leitor['nomeLeitor'], leitor['ip'])
        else:
            logging.error('Leitor com ID %s não encontrado', leitor_id)
            
        return leitor
        
    except Exception as e:
        logging.error('Erro ao buscar leitor %s: %s', leitor_id, str(e))
        return None

def sincronizarLeitorForcado(leitor_id, max_retries=3, retry_delay=5):
    """
    Força a sincronização de TODAS as imagens para um leitor específico.
    Ignora o histórico de sincronizações anteriores.
    
    Args:
        leitor_id: ID do leitor
        max_retries: Número máximo de tentativas
        retry_delay: Delay em segundos entre tentativas
        
    Returns:
        dict: Resultado com sucesso, total de imagens e mensagens
    """
    resultado = {
        'sucesso': False,
        'total_pessoas': 0,
        'total_imagens_enviadas': 0,
        'erros': [],
        'mensagem': ''
    }
    
    # Busca o leitor
    leitor = buscarLeitor(leitor_id)
    if not leitor:
        resultado['mensagem'] = f'Leitor com ID {leitor_id} não encontrado'
        return resultado
    
    # Verifica se está ativo e configurado
    if leitor.get('status') != 'T':
        resultado['mensagem'] = f'Leitor {leitor["nomeLeitor"]} está inativo'
        logging.warning(resultado['mensagem'])
        return resultado
    
    if leitor.get('configurado') != 'T':
        resultado['mensagem'] = f'Leitor {leitor["nomeLeitor"]} não está configurado'
        logging.warning(resultado['mensagem'])
        return resultado
    
    logging.info('Iniciando sincronização FORÇADA para o leitor %s (ID: %s)', 
                 leitor['nomeLeitor'], leitor_id)
    
    for attempt in range(max_retries):
        try:
            # Valida sessão
            session = isSessionValid(leitor)
            if not session:
                logging.error('Sessão inválida para o leitor %s (tentativa %d/%d)', 
                            leitor['nomeLeitor'], attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    resultado['mensagem'] = 'Falha ao validar sessão do leitor'
                    return resultado
            
            leitor['session'] = session
            
            # Busca TODAS as pessoas com credenciais ativas
            conn = conectarBancoEvento()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT DISTINCT p.id, p.nome
                FROM tblPessoa p
                INNER JOIN tblCredencial c ON p.id = c.idPessoa
                WHERE c.status = 'T' AND p.status = 'T'
                ORDER BY p.nome
            """)
            pessoas = cursor.fetchall()
            
            if not pessoas:
                resultado['sucesso'] = True
                resultado['mensagem'] = 'Nenhuma pessoa com credencial ativa encontrada'
                logging.info(resultado['mensagem'])
                cursor.close()
                conn.close()
                return resultado
            
            resultado['total_pessoas'] = len(pessoas)
            logging.info('Encontradas %d pessoas com credenciais ativas', len(pessoas))
            
            user_images = []
            
            for pessoa in pessoas:
                # Busca a imagem mais recente (IGNORA se já foi sincronizada)
                cursor.execute("""
                    SELECT a.id, a.pathLocal, a.pathNuvem
                    FROM tblArquivo a
                    WHERE a.idReferencia = %s 
                    AND a.tipoReferencia = 'PESSOA'
                    AND a.tipoArquivo = 'AVATAR'
                    ORDER BY a.dataCadastro DESC 
                    LIMIT 1
                """, (pessoa['id'],))
                
                arquivo = cursor.fetchone()
                
                if arquivo:
                    # Lê a imagem do disco e converte para base64
                    imagem_base64 = lerImagemBase64(arquivo['pathLocal'], arquivo['pathNuvem'])
                    
                    if not imagem_base64:
                        erro = f'Imagem não encontrada para pessoa {pessoa["nome"]} (arquivo {arquivo["id"]})'
                        logging.warning(erro)
                        resultado['erros'].append(erro)
                        continue
                    
                    # Verifica/cria usuário no leitor
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
                                    erro = f'Falha ao criar usuário {pessoa["nome"]}: {create_user_response.text}'
                                    logging.error(erro)
                                    resultado['erros'].append(erro)
                                    continue
                                else:
                                    logging.info('Usuário %s criado no leitor', pessoa['nome'])
                        
                        # Adiciona à lista para envio
                        user_images.append({
                            'user_id': pessoa['id'],
                            'user_name': pessoa['nome'],
                            'timestamp': int(time.time()),
                            'image': imagem_base64,
                            'arquivo_id': arquivo['id']
                        })
                        
                    except requests.exceptions.RequestException as e:
                        erro = f'Erro ao verificar/criar usuário {pessoa["nome"]}: {str(e)}'
                        logging.error(erro)
                        resultado['erros'].append(erro)
                        continue
                else:
                    erro = f'Nenhuma imagem encontrada para pessoa {pessoa["nome"]}'
                    logging.warning(erro)
                    resultado['erros'].append(erro)
            
            cursor.close()
            conn.close()
            
            # Envia as imagens
            if user_images:
                logging.info('Enviando %d imagens FORÇADAS para o leitor %s', 
                           len(user_images), leitor['nomeLeitor'])
                
                sucesso = enviarImagensEmLotes(leitor, session, user_images, forcado=True)
                
                if sucesso:
                    resultado['sucesso'] = True
                    resultado['total_imagens_enviadas'] = len(user_images)
                    resultado['mensagem'] = f'Sincronização forçada concluída: {len(user_images)} imagens enviadas'
                    logging.info(resultado['mensagem'])
                else:
                    resultado['mensagem'] = 'Falha ao enviar algumas imagens'
                    logging.error(resultado['mensagem'])
            else:
                resultado['mensagem'] = 'Nenhuma imagem válida para sincronizar'
                logging.info(resultado['mensagem'])
            
            return resultado
            
        except Exception as e:
            erro = f'Erro na sincronização (tentativa {attempt + 1}/{max_retries}): {str(e)}'
            logging.error(erro)
            resultado['erros'].append(erro)
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                resultado['mensagem'] = f'Falha após {max_retries} tentativas'
                return resultado
    
    return resultado

def enviarImagensEmLotes(leitor, session, user_images, batch_size=2 * 1024 * 1024, forcado=False):
    """
    Envia imagens em lotes para não exceder o tamanho máximo da requisição.
    
    Args:
        leitor: Dados do leitor
        session: Sessão válida
        user_images: Lista de imagens a enviar
        batch_size: Tamanho máximo do lote em bytes
        forcado: Se True, marca como sincronização forçada
        
    Returns:
        bool: True se todas as imagens foram enviadas com sucesso
    """
    current_batch = []
    current_size = 0
    sucesso_geral = True
    
    for image_data in user_images:
        image_size = len(image_data['image'].encode('utf-8')) if image_data['image'] else 0
        
        if current_size + image_size > batch_size and current_batch:
            if not enviarLote(leitor, session, current_batch, forcado):
                sucesso_geral = False
            current_batch = []
            current_size = 0
        
        current_batch.append(image_data)
        current_size += image_size
    
    if current_batch:
        if not enviarLote(leitor, session, current_batch, forcado):
            sucesso_geral = False
    
    return sucesso_geral

def enviarLote(leitor, session, batch, forcado=False, max_retries=3, retry_delay=5):
    """
    Envia um lote de imagens para o leitor facial.
    
    Args:
        leitor: Dados do leitor
        session: Sessão válida
        batch: Lista de imagens do lote
        forcado: Se True, marca como sincronização forçada
        max_retries: Número máximo de tentativas
        retry_delay: Delay entre tentativas
        
    Returns:
        bool: True se o lote foi enviado com sucesso
    """
    conn = None
    cursor = None
    
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor()
        
        for attempt in range(max_retries):
            try:
                # Verifica sessão
                session_check = isSessionValid(leitor)
                if not session_check:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return False
                
                session = session_check
                
                # Prepara payload
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
                
                # Registra o resultado
                for image_data in batch:
                    sucesso = response.status_code == 200
                    
                    if sucesso:
                        mensagem = "Imagem sincronizada (FORÇADO)" if forcado else "Imagem sincronizada"
                        status = 1
                    else:
                        mensagem = f"Falha na sincronização forçada: {response.text[:200]}"
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
                    logging.info('Lote de %d imagens enviado com sucesso', len(batch))
                    return True
                else:
                    logging.error('Falha ao enviar lote: %s', response.text)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                    
            except requests.exceptions.RequestException as e:
                logging.error('Erro ao enviar lote (tentativa %d/%d): %s', attempt + 1, max_retries, str(e))
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    # Registra falha
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
                    return False
                    
    except Exception as e:
        logging.error('Erro inesperado ao enviar lote: %s', str(e))
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python sincronizarLeitor.py <id_leitor>")
        print("Exemplo: python sincronizarLeitor.py 5")
        sys.exit(1)
    
    try:
        leitor_id = int(sys.argv[1])
    except ValueError:
        print("Erro: ID do leitor deve ser um número inteiro")
        sys.exit(1)
    
    logging.info('='*60)
    logging.info('INICIANDO SINCRONIZAÇÃO FORÇADA - Leitor ID: %s', leitor_id)
    logging.info('='*60)
    
    inicio = time.time()
    resultado = sincronizarLeitorForcado(leitor_id)
    duracao = time.time() - inicio
    
    # Log do resultado
    logging.info('='*60)
    logging.info('RESULTADO DA SINCRONIZAÇÃO FORÇADA')
    logging.info('Sucesso: %s', resultado['sucesso'])
    logging.info('Total de pessoas: %d', resultado['total_pessoas'])
    logging.info('Total de imagens enviadas: %d', resultado['total_imagens_enviadas'])
    logging.info('Total de erros: %d', len(resultado['erros']))
    logging.info('Mensagem: %s', resultado['mensagem'])
    logging.info('Duração: %.2f segundos', duracao)
    logging.info('='*60)
    
    # Saída para o PHP
    import json
    print(json.dumps({
        'sucesso': resultado['sucesso'],
        'total_pessoas': resultado['total_pessoas'],
        'total_imagens_enviadas': resultado['total_imagens_enviadas'],
        'total_erros': len(resultado['erros']),
        'erros': resultado['erros'][:10],  # Primeiros 10 erros apenas
        'mensagem': resultado['mensagem'],
        'duracao_segundos': round(duracao, 2)
    }, ensure_ascii=False))
    
    sys.exit(0 if resultado['sucesso'] else 1)

if __name__ == '__main__':
    main()

