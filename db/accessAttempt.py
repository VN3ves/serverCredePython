from datetime import datetime
from db import connection_pool

def register_facial_access_attempt(
    user_id: int,
    leitor_id: int,
    success: bool,
    message: str,
    event_id: int,
    credential_id: int = None,
    setor_id: int = None,
    data_tentativa: datetime = None,
    tipo_entrada: str = 'ENTRADA',
    credential: dict = None,
    idLote: int = None,
):
    """
    Registra uma tentativa de acesso na tblEntradas de acordo com a nova estrutura.
    """
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        # Se a coluna 'id' é AUTO_INCREMENT, não precisa passar o valor
        sql = """
            INSERT INTO tblEntradas
                (idEvento, idPessoa, idCredencial, idSetor,
                 idLeitor, credencial, tipoEntrada, permitida, mensagem,
                 dataTentativa, idLote)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            event_id,
            user_id,
            credential_id,
            setor_id,
            leitor_id,
            credential,
            tipo_entrada,
            'T' if success else 'F',
            message,
            data_tentativa if data_tentativa else datetime.now(),
            idLote
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
        