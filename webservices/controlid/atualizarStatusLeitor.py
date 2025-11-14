import time
import logging
from db.funcoes import (
    findLeitores,
    updateLeitor,
)
from datetime import datetime, timedelta

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
            