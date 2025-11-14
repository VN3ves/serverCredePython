import uuid
from datetime import datetime
from db import connection_pool

def register_facial_access_attempt(
    user_id: str,
    leitor_id: str,
    success: bool,
    message: str,
    event_id: int,
    credential_id: str = None,
    setor_id: str = None,
    terminal_id: str = None,
    data_tentativa: datetime = None,
    tipo_entrada: str = 'ENTRADA',
):
    """
    Registra uma tentativa de acesso na tblEntradas de acordo com a nova estrutura.
    """
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO tblEntradas
                (id, idEvento, idPessoa, idCredencial, idSetor,
                 idLeitor, idTerminal, tipoEntrada, permitida, mensagem,
                 dataTentativa)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s)
        """
        cursor.execute(sql, (
            str(uuid.uuid4()),  # Gera um novo ID CHAR(36)
            event_id,
            user_id,
            credential_id,
            setor_id,
            leitor_id,
            terminal_id,
            tipo_entrada,
            'T' if success else 'F',
            message,
            data_tentativa if data_tentativa else datetime.now()
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
        
def register_access_attempt(
    credential_id: int,
    success: bool,
    message: str,
    setor_id: int = None,
    terminal_id: int = None,
    data_tentativa: datetime = None,
    tipo_entrada: str = 'ENTRADA',
):
    """
    Registra uma tentativa de acesso em tblEntradas, usando 'TERMINAL' como tipoEntrada.
    """
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO tblEntradas
                (idPessoa, idTerminal, idCredencial, idSetor,
                 tipoEntrada, permitida, mensagem,
                 deviceIdLeitor, deviceIdTerminal,
                 dataTentativa)
            VALUES (%s,        %s,         %s,          %s,
                    %s,         %s,         %s,
                    %s,           %s,
                    %s)
        """
        cursor.execute(sql, (
            None,                             # idPessoa (não usado em terminais)
            terminal_id,                      # idTerminal
            credential_id,                    # idCredencial
            setor_id,                         # idSetor
            tipo_entrada,                      # tipoEntrada
            'T' if success else 'F',          # permitida
            message,                          # mensagem
            None,                             # deviceIdLeitor
            None,                             # deviceIdTerminal (pode ser NULL)
            data_tentativa if data_tentativa else datetime.now()
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()