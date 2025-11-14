from datetime import datetime
from db import conectarBancoEvento
import pytz

def handle_device_alive(device_id: str):
    """
    Se existir um registro com este device_id,
    atualiza status para 1 e atualiza o timestamp.
    """
    conn = conectarBancoEvento()
    cursor = conn.cursor()
    try:
        sql = """
            UPDATE tblLeitor
               SET condicao   = %s,
                   dataEdicao = %s,
                   dataMonitoramento = %s
             WHERE deviceId = %s
        """
        now = datetime.now(pytz.timezone("America/Sao_Paulo"))
        cursor.execute(sql, ('ON', now, now, device_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
