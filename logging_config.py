"""
Configuração centralizada de logging para o sistema.

Este módulo centraliza toda a configuração de logging, garantindo que cada módulo
possa ter seu próprio arquivo de log sem conflitos.

Uso:
    from logging_config import get_logger
    
    logger = get_logger('configurarLeitor')
    logger.info('Mensagem de log')
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Diretório de logs
LOG_DIR = '/var/www/logs'

# Formato padrão para todos os logs
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Dicionário de loggers já criados (cache)
_loggers = {}

def get_logger(nome_modulo, nivel=logging.INFO, arquivo_log=None):
    """
    Retorna um logger configurado para o módulo especificado.
    
    Args:
        nome_modulo: Nome do módulo (ex: 'configurarLeitor', 'sincronizarImagens')
        nivel: Nível de log (default: logging.INFO)
        arquivo_log: Nome do arquivo de log (se None, usa f'log{nome_modulo}.log')
    
    Returns:
        logging.Logger: Logger configurado
    """
    # Retorna do cache se já existir
    if nome_modulo in _loggers:
        return _loggers[nome_modulo]
    
    # Define o arquivo de log
    if arquivo_log is None:
        arquivo_log = f'log{nome_modulo}.log'
    
    caminho_completo = os.path.join(LOG_DIR, arquivo_log)
    
    # Cria o logger
    logger = logging.getLogger(nome_modulo)
    logger.setLevel(nivel)
    
    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers.clear()
    
    # Cria handler de arquivo com rotação (10MB por arquivo, mantém 5 backups)
    file_handler = RotatingFileHandler(
        caminho_completo,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(nivel)
    
    # Define o formato
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(formatter)
    
    # Adiciona o handler ao logger
    logger.addHandler(file_handler)
    
    # Evita propagação para o logger raiz
    logger.propagate = False
    
    # Armazena no cache
    _loggers[nome_modulo] = logger
    
    return logger

def get_cron_logger():
    """Retorna logger para o cron."""
    return get_logger('Cron', arquivo_log='cronControl.log')

def get_config_leitor_logger():
    """Retorna logger para configuração de leitores."""
    return get_logger('ConfigLeitor', arquivo_log='logConfigLeitor.log')

def get_sincronizar_imagens_logger():
    """Retorna logger para sincronização de imagens."""
    return get_logger('SincronizarImagens', arquivo_log='logSincronizarImagens.log')

def get_processar_jobs_logger():
    """Retorna logger para processamento de jobs."""
    return get_logger('ProcessarJobs', arquivo_log='logProcessarJobsSync.log')

def get_atualizar_status_logger():
    """Retorna logger para atualização de status."""
    return get_logger('AtualizarStatus', arquivo_log='logAtualizarStatus.log')

def get_banco_logger():
    """Retorna logger para erros de banco de dados."""
    return get_logger('Banco', arquivo_log='errosBanco.log', nivel=logging.ERROR)

def get_server_logger():
    """Retorna logger para o servidor principal."""
    return get_logger('Server', arquivo_log='server.log')

