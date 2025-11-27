import time
from db.funcoes import (
    findLeitores,
    updateLeitor,
)
from datetime import datetime, timedelta
from logging_config import get_atualizar_status_logger

# Obtém o logger configurado para este módulo
logging = get_atualizar_status_logger()

def monitorarLeitores():
    try:
        leitores = findLeitores()
        for leitor in leitores:
            dataMonitoramento = leitor['dataMonitoramento']
            if dataMonitoramento:
                if (datetime.now() - dataMonitoramento).total_seconds() > 60:
                    updateLeitor(leitor['id'], {'condicao': 'OFF'})
                    
    except Exception as e:
        logging.error(f"Erro ao monitorar leitores: {e}")
            