# cron_control.py
import datetime
import os
import sys
from webservices.controlid.configurarLeitor import configurarLeitor
from webservices.controlid.atualizarStatusLeitor import monitorarLeitores
from webservices.controlid.sincronizarImagens import sincronizarImagens

# Configura o timezone, se necessário
os.environ['TZ'] = 'America/Sao_Paulo'

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    
    with open("/var/www/logs/cronControl.log", "a") as f:
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def roda_chamada_manual():
    log("Executando chamada manual")
    #configurarLeitor()
    sincronizarImagens()
    log("Chamada manual concluída")
    
def tarefa_1_min():
    monitorarLeitores()
    
def tarefa_5_min():
    configurarLeitor()
    sincronizarImagens()

def main():
    now = datetime.datetime.now()
    
    # A cada minuto
    tarefa_1_min()
    
    # A cada 2 minutos
    # if now.minute % 2 == 0:
    #     tarefa_2_min()

    # A cada 5 minutos
    if now.minute % 5 == 0:
        tarefa_5_min()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "manual": 
        roda_chamada_manual()
    else:
        try:
            main()
        except Exception as e:
            log(f"Erro: {e}")