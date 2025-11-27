# cron_control.py
import datetime
import os
import sys
import asyncio
from webservices.controlid.configurarLeitor import configurarLeitor
from webservices.controlid.atualizarStatusLeitor import monitorarLeitores
from webservices.controlid.sincronizarImagens import sincronizarImagens
from logging_config import get_cron_logger

# Configura o timezone, se necessário
os.environ['TZ'] = 'America/Sao_Paulo'

# Obtém o logger configurado para este módulo
logger = get_cron_logger()

def log(msg):
    """Função de compatibilidade - usa o logger configurado"""
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    logger.info(msg)

def roda_chamada_manual():
    log("Executando chamada manual")
    #configurarLeitor()
    sincronizarImagens()
    log("Chamada manual concluída")
    
def tarefa_1_min():
    monitorarLeitores()
    
def tarefa_3_min():
    sincronizarImagens()
    
async def tarefa_5_min():
    await configurarLeitor()

def main():
    now = datetime.datetime.now()
    
    # A cada minuto
    tarefa_1_min()
    
    # A cada 3 minutos
    if now.minute % 3 == 0:
        tarefa_3_min()

    # A cada 5 minutos
    if now.minute % 5 == 0:
        asyncio.run(tarefa_5_min())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "manual": 
        roda_chamada_manual()
    else:
        try:
            main()
        except Exception as e:
            log(f"Erro: {e}")