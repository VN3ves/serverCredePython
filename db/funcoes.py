import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from db import conectarBancoEvento, connection_pool

logging.basicConfig(
    filename='/var/www/logs/errosBanco.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def getEventoBanco(codigo: str):
    try:
        """
        Obtém o nome do banco de dados do servidor com base no código informado.
        Retorna o nome do banco de dados ou None se não encontrar.
        """
        conn = connection_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT tblEventoBanco.nomeBanco
            FROM tblEvento
            INNER JOIN tblEventoServidor ON tblEvento.id = tblEventoServidor.idEvento
            INNER JOIN tblServidor ON tblEventoServidor.idServidor = tblServidor.id
            INNER JOIN tblEventoBanco ON tblEvento.id = tblEventoBanco.idEvento
            WHERE tblServidor.status = 'T' AND tblServidor.codigo = %s
            LIMIT 1
        """

        cursor.execute(query, (codigo,))
        evento = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return evento['nomeBanco'] if evento else None
    except Exception as e:
        logging.error(f"Erro ao obter o nome do banco de dados: {e}")
        return None

def findLeitores():
    conn = conectarBancoEvento()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tblLeitor")
    leitores = cursor.fetchall()
    cursor.close()
    conn.close()
    logging.info('Leitores faciais encontrados: %s', leitores)
    return leitores

def findLeitoresParaConfigurar():
    conn = conectarBancoEvento()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tblLeitor WHERE configurado = 'F'")
    leitores = cursor.fetchall()
    cursor.close()
    conn.close()
    logging.info('Leitores faciais encontrados: %s', leitores)
    return leitores

def updateLeitor(leitor_id: str, campos: dict):
    """
    Atualiza campos da tabela tblLeitor com base no ID do leitor.
    
    :param leitor_id: ID do leitor a ser atualizado
    :param campos: dicionário com os campos e valores a serem atualizados
    """
    if not campos:
        logging.warning("Nenhum campo fornecido para atualização do leitor %s", leitor_id)
        return

    conn = conectarBancoEvento()
    cursor = conn.cursor()

    try:
        set_clause = ', '.join([f"{col} = %s" for col in campos.keys()])
        valores = list(campos.values()) + [leitor_id]

        sql = f"UPDATE tblLeitor SET {set_clause} WHERE id = %s"
        cursor.execute(sql, valores)
        conn.commit()

        logging.info("Leitor %s atualizado com os campos: %s", leitor_id, list(campos.keys()))
    except Exception as e:
        logging.error("Erro ao atualizar leitor %s: %s", leitor_id, e)
    finally:
        cursor.close()
        conn.close()

def marcarLeitorConfigurado(leitor_id):
    conn = conectarBancoEvento()
    cursor = conn.cursor()
    cursor.execute("UPDATE tblLeitor SET configurado = 'T' WHERE id = %s", (leitor_id,))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('Leitor %s marcado como configurado', leitor_id)

def updateLeitorSession(leitor_id, session):
    conn = conectarBancoEvento()
    cursor = conn.cursor()
    cursor.execute("UPDATE tblLeitor SET session = %s WHERE id = %s", (session, leitor_id))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('Sessão atualizada para o leitor %s: %s', leitor_id, session)

def updateLeitorDeviceId(leitor_id, device_id):
    conn = conectarBancoEvento()
    cursor = conn.cursor()
    cursor.execute("UPDATE tblLeitor SET deviceId = %s WHERE id = %s", (device_id, leitor_id))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('ID do dispositivo atualizado para o leitor %s: %s', leitor_id, device_id)

def updateLeitorServerId(leitor_id, server_id):
    conn = conectarBancoEvento()
    cursor = conn.cursor()
    cursor.execute("UPDATE tblLeitor SET serverId = %s WHERE id = %s", (server_id, leitor_id))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info('ID do servidor atualizado para o leitor %s: %s', leitor_id, server_id)