#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de Jobs de Sincronização de Imagens.
Similar ao sistema de queue/jobs do Laravel.

Este script processa a tabela tblJobSync, enviando imagens específicas para todos os leitores
quando uma nova foto é cadastrada no sistema.

Uso:
    python processarJobsSync.py [--limit N] [--job-id ID]
    
Exemplos:
    python processarJobsSync.py                    # Processa até 10 jobs pendentes
    python processarJobsSync.py --limit 50         # Processa até 50 jobs
    python processarJobsSync.py --job-id 123       # Processa apenas o job 123
"""

import sys
import os

# Adiciona o diretório raiz do servidor ao path para permitir importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
import time
import logging
import json
import argparse
import base64
from datetime import datetime, timedelta
from contextlib import contextmanager
import fcntl
from db import conectarBancoEvento
from webservices.controlid.configurarLeitor import isSessionValid
from config import SISTEMA_GERENCIAMENTO

# Configuração de logging
logging.basicConfig(
    filename='/var/www/logs/logProcessarJobsSync.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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

@contextmanager
def file_lock(lock_path):
    """Context manager para lock de arquivo"""
    lock_file = None
    try:
        lock_file = open(lock_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        logging.info('Lock adquirido')
        yield lock_file
    except IOError:
        logging.warning('Outro processo já está executando')
        raise
    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                logging.info('Lock liberado')
            except Exception as e:
                logging.error('Erro ao liberar lock: %s', str(e))

def buscarJobsPendentes(limit=10, job_id=None):
    """
    Busca jobs pendentes ou prontos para reprocessar.
    
    Args:
        limit: Número máximo de jobs a retornar
        job_id: Se fornecido, busca apenas este job específico
        
    Returns:
        list: Lista de jobs pendentes
    """
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor(dictionary=True)
        
        if job_id:
            # Busca job específico
            cursor.execute("""
                SELECT * FROM tblJobSync
                WHERE id = %s
                LIMIT 1
            """, (job_id,))
        else:
            # Busca jobs pendentes ou que falharam mas podem tentar novamente
            cursor.execute("""
                SELECT * FROM tblJobSync
                WHERE (
                    status = 'PENDENTE' 
                    OR (
                        status = 'FALHA' 
                        AND tentativas < maxTentativas 
                    )
                )
                ORDER BY dataAgendamento ASC
                LIMIT %s
            """, (limit,))
        
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        logging.info('Encontrados %d jobs para processar', len(jobs))
        return jobs
        
    except Exception as e:
        logging.error('Erro ao buscar jobs pendentes: %s', str(e))
        return []

def marcarJobComoProcessando(job_id):
    """
    Marca um job como PROCESSANDO e incrementa tentativas.
    
    Args:
        job_id: ID do job
        
    Returns:
        bool: True se marcado com sucesso
    """
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tblJobSync
            SET status = 'PROCESSANDO',
                tentativas = tentativas + 1,
                dataInicio = NOW()
            WHERE id = %s
        """, (job_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logging.info('Job %d marcado como PROCESSANDO', job_id)
        return True
        
    except Exception as e:
        logging.error('Erro ao marcar job %d como processando: %s', job_id, str(e))
        return False

def marcarJobComoConcluido(job_id):
    """
    Marca um job como CONCLUIDO.
    
    Args:
        job_id: ID do job
    """
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tblJobSync
            SET status = 'CONCLUIDO',
                dataConclusao = NOW(),
                mensagemErro = NULL
            WHERE id = %s
        """, (job_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logging.info('Job %d marcado como CONCLUIDO', job_id)
        
    except Exception as e:
        logging.error('Erro ao marcar job %d como concluído: %s', job_id, str(e))

def marcarJobComoFalha(job_id, mensagem_erro, tentativas, max_tentativas):
    """
    Marca um job como FALHA ou volta para PENDENTE se ainda há tentativas.
    
    Args:
        job_id: ID do job
        mensagem_erro: Mensagem de erro
        tentativas: Número atual de tentativas
        max_tentativas: Máximo de tentativas permitidas
    """
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor()
        
        if tentativas >= max_tentativas:
            # Falha definitiva
            cursor.execute("""
                UPDATE tblJobSync
                SET status = 'FALHA',
                    mensagemErro = %s,
                    dataConclusao = NOW()
                WHERE id = %s
            """, (mensagem_erro, job_id))
            logging.error('Job %d marcado como FALHA definitiva após %d tentativas', job_id, tentativas)
        else:
            # Aguarda para próxima tentativa (delay exponencial)
            cursor.execute("""
                UPDATE tblJobSync
                SET status = 'PENDENTE',
                    mensagemErro = %s
                WHERE id = %s
            """, (mensagem_erro, job_id))
            logging.warning('Job %d voltou para PENDENTE.', job_id)
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logging.error('Erro ao marcar job %d como falha: %s', job_id, str(e))

def buscarLeitoresAtivos():
    """
    Busca todos os leitores ativos e configurados.
    
    Returns:
        list: Lista de leitores
    """
    try:
        conn = conectarBancoEvento()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM tblLeitor
            WHERE status = 'T' AND configurado = 'T'
            ORDER BY nomeLeitor
        """)
        
        leitores = cursor.fetchall()
        cursor.close()
        conn.close()
        
        logging.info('Encontrados %d leitores ativos', len(leitores))
        return leitores
        
    except Exception as e:
        logging.error('Erro ao buscar leitores ativos: %s', str(e))
        return []

def processarJobSyncImagem(job):
    """
    Processa um job de sincronização de imagem.
    Envia a imagem para todos os leitores ativos.
    
    Args:
        job: Dados do job
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    job_id = job['id']
    pessoa_id = job['idPessoa']
    arquivo_id = job['idArquivo']
    
    logging.info('Processando job %d: Sincronizar imagem do arquivo %d (pessoa %d)', 
                 job_id, arquivo_id, pessoa_id)
    
    try:
        # Busca informações da pessoa e arquivo
        conn = conectarBancoEvento()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.id, p.nome, a.pathLocal, a.pathNuvem
            FROM tblPessoa p
            INNER JOIN tblArquivo a ON a.idReferencia = p.id
            WHERE p.id = %s AND a.id = %s
            AND a.tipoReferencia = 'PESSOA' AND a.tipoArquivo = 'AVATAR'
            LIMIT 1
        """, (pessoa_id, arquivo_id))
        
        dados = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not dados:
            return False, f'Pessoa ou arquivo não encontrado (pessoa: {pessoa_id}, arquivo: {arquivo_id})'
        
        # Lê a imagem do disco e converte para base64
        imagem_base64 = lerImagemBase64(dados['pathLocal'], dados['pathNuvem'])
        
        if not imagem_base64:
            return False, 'Imagem não encontrada ou erro ao ler arquivo'
        
        # Busca leitores ativos
        leitores = buscarLeitoresAtivos()
        if not leitores:
            return False, 'Nenhum leitor ativo encontrado'
        
        # Envia para cada leitor
        erros = []
        sucessos = 0
        
        for leitor in leitores:
            try:
                # Valida sessão
                session = isSessionValid(leitor)
                if not session:
                    erros.append(f'Leitor {leitor["nomeLeitor"]}: sessão inválida')
                    continue
                
                # Verifica se usuário existe no leitor
                user_exists_response = requests.post(
                    f"http://{leitor['ip']}/load_objects.fcgi?session={session}",
                    json={
                        'object': 'users',
                        'where': [{'object': 'users', 'field': 'id', 'operator': '=', 'value': pessoa_id}]
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                
                if user_exists_response.status_code == 200:
                    users = user_exists_response.json().get('users', [])
                    if not users:
                        # Cria usuário
                        create_user_response = requests.post(
                            f"http://{leitor['ip']}/create_objects.fcgi?session={session}",
                            json={
                                'object': 'users',
                                'values': [{
                                    'id': pessoa_id,
                                    'registration': str(pessoa_id),
                                    'name': dados['nome']
                                }]
                            },
                            headers={'Content-Type': 'application/json'},
                            timeout=5
                        )
                        
                        if create_user_response.status_code != 200:
                            erros.append(f'Leitor {leitor["nomeLeitor"]}: falha ao criar usuário')
                            continue
                
                # Envia a imagem
                response = requests.post(
                    f"http://{leitor['ip']}/user_set_image_list.fcgi?session={session}",
                    json={
                        'match': False,
                        'user_images': [{
                            'user_id': pessoa_id,
                            'timestamp': int(time.time()),
                            'image': imagem_base64
                        }]
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=90
                )
                
                # Registra resultado
                conn = conectarBancoEvento()
                cursor = conn.cursor()
                
                if response.status_code == 200:
                    sucessos += 1
                    cursor.execute("""
                        INSERT INTO tblLeitorFoto (idEvento, idLeitor, idArquivo, status, mensagem, dataCadastro)
                        VALUES (%s, %s, %s, 1, 'Sincronizado via job', NOW())
                    """, (leitor['idEvento'], leitor['id'], arquivo_id))
                    logging.info('Imagem enviada com sucesso para o leitor %s', leitor['nomeLeitor'])
                else:
                    erros.append(f'Leitor {leitor["nomeLeitor"]}: {response.text[:100]}')
                    cursor.execute("""
                        INSERT INTO tblLeitorFoto (idEvento, idLeitor, idArquivo, status, mensagem, dataCadastro)
                        VALUES (%s, %s, %s, 0, %s, NOW())
                    """, (leitor['idEvento'], leitor['id'], arquivo_id, f'Erro: {response.text[:200]}'))
                
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                erro_msg = f'Leitor {leitor["nomeLeitor"]}: {str(e)}'
                logging.error(erro_msg)
                erros.append(erro_msg)
        
        # Resultado final
        if sucessos == 0:
            return False, f'Falha em todos os leitores. Erros: {"; ".join(erros[:3])}'
        elif sucessos == len(leitores):
            return True, f'Imagem enviada para {sucessos} leitor(es) com sucesso'
        else:
            return True, f'Enviado para {sucessos}/{len(leitores)} leitores. Alguns erros: {"; ".join(erros[:2])}'
        
    except Exception as e:
        return False, f'Erro inesperado: {str(e)}'

def processarJob(job):
    """
    Processa um job de acordo com seu tipo.
    
    Args:
        job: Dados do job
        
    Returns:
        bool: True se processado com sucesso
    """
    job_id = job['id']
    
    # Marca como processando
    if not marcarJobComoProcessando(job_id):
        return False
    
    try:
        sucesso, mensagem = processarJobSyncImagem(job)
        
        # Marca resultado
        if sucesso:
            marcarJobComoConcluido(job_id)
            logging.info('Job %d concluído: %s', job_id, mensagem)
        else:
            marcarJobComoFalha(job_id, mensagem, job['tentativas'] + 1, job['maxTentativas'])
            logging.error('Job %d falhou: %s', job_id, mensagem)
        
        return sucesso
        
    except Exception as e:
        mensagem = f'Erro ao processar job: {str(e)}'
        marcarJobComoFalha(job_id, mensagem, job['tentativas'] + 1, job['maxTentativas'])
        logging.error('Job %d - %s', job_id, mensagem)
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Processa jobs de sincronização de imagens')
    parser.add_argument('--limit', type=int, default=10, help='Número máximo de jobs a processar')
    parser.add_argument('--job-id', type=int, help='Processar apenas um job específico')
    args = parser.parse_args()
    
    lock_file_path = '/tmp/processar_jobs_sync.lock'
    
    try:
        with file_lock(lock_file_path):
            logging.info('='*60)
            logging.info('INICIANDO PROCESSAMENTO DE JOBS')
            logging.info('='*60)
            
            inicio = time.time()
            
            # Busca jobs pendentes
            jobs = buscarJobsPendentes(limit=args.limit, job_id=args.job_id)
            
            if not jobs:
                logging.info('Nenhum job pendente para processar')
                print(json.dumps({'sucesso': True, 'jobs_processados': 0, 'mensagem': 'Nenhum job pendente'}))
                return
            
            # Processa cada job
            total_processados = 0
            total_sucesso = 0
            total_falha = 0
            
            for job in jobs:
                logging.info('Processando job %d (tentativa %d/%d)', 
                           job['id'], job['tentativas'] + 1, job['maxTentativas'])
                
                if processarJob(job):
                    total_sucesso += 1
                else:
                    total_falha += 1
                
                total_processados += 1
            
            duracao = time.time() - inicio
            
            # Log final
            logging.info('='*60)
            logging.info('PROCESSAMENTO FINALIZADO')
            logging.info('Jobs processados: %d', total_processados)
            logging.info('Sucessos: %d', total_sucesso)
            logging.info('Falhas: %d', total_falha)
            logging.info('Duração: %.2f segundos', duracao)
            logging.info('='*60)
            
            # Saída para o PHP
            print(json.dumps({
                'sucesso': True,
                'jobs_processados': total_processados,
                'sucessos': total_sucesso,
                'falhas': total_falha,
                'duracao_segundos': round(duracao, 2)
            }, ensure_ascii=False))
            
    except IOError:
        print(json.dumps({'sucesso': False, 'mensagem': 'Outro processo já está executando'}))
        sys.exit(1)
    except Exception as e:
        logging.error('Erro fatal: %s', str(e), exc_info=True)
        print(json.dumps({'sucesso': False, 'mensagem': f'Erro: {str(e)}'}))
        sys.exit(1)

if __name__ == '__main__':
    main()

