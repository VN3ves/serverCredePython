from datetime import datetime, timedelta
from db import connection_pool
from db.accessAttempt import register_facial_access_attempt

def handle_user_identified(
    device_id: str,
    user_id: str,
    event,
    duress,
    face_mask,
    time,
    portal_id,
    uuid,
    block_read_data,
    block_read_error,
    card_value,
    qrcode_value,
    uhf_tag,
    pin_value,
    user_has_image,
    user_name: str,
    password,
    confidence,
    log_type_id
):
    """
    Lógica de validação de acesso usando as novas tabelas.
    Retorna um dicionário pronto para ser convertido em JSON.
    """
    # Converte IDs para inteiros e garante que user_name seja string (igual ao PHP)
    try:
        user_id = int(user_id)
        portal_id = int(portal_id) if portal_id else 0
        user_name = str(user_name) if user_name else ''
    except (ValueError, TypeError):
        return {
            'result': {
                'event': 2,
                'message': 'Parâmetros de identificação inválidos.',
                'user_id': 0,
                'user_name': '',
                'user_image': False,
                'portal_id': 0
            }
        }
    
    conn = connection_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1) Leitor existe?
        cursor.execute(
            "SELECT id, idEvento, idSetor FROM tblLeitor WHERE deviceId = %s AND status = 'T' LIMIT 1",
            (device_id,)
        )
        leitor = cursor.fetchone()
        if not leitor:
            # Não é possível registrar o evento se o leitor não for encontrado
            return {
                'result': {
                    'event': 1,
                    'message': 'Equipamento inválido.',
                    'user_id': user_id,
                    'user_name': user_name,
                    'user_image': False,
                    'portal_id': portal_id
                }
            }

        event_id = leitor['idEvento']
        setor_id = leitor['idSetor']
        leitor_id = leitor['id']

        # 2) Usuário existe?
        cursor.execute("SELECT id FROM tblPessoa WHERE id = %s AND status = 'T' LIMIT 1", (user_id,))
        pessoa = cursor.fetchone()
        if not pessoa:
            register_facial_access_attempt(user_id, leitor_id, False, 'Usuário não encontrado.', event_id, setor_id=setor_id)
            return {
                'result': {
                    'event': 3,
                    'message': 'Usuário não encontrado.',
                    'user_id': user_id,
                    'user_name': user_name,
                    'user_image': False
                }
            }

        # 3) Última credencial ativa da pessoa
        cursor.execute(
            "SELECT id, idLote, codigoCredencial FROM tblCredencial WHERE idPessoa = %s AND status = 'T' ORDER BY dataCadastro DESC LIMIT 1",
            (user_id,)
        )
        cred = cursor.fetchone()
        if not cred:
            register_facial_access_attempt(user_id, leitor_id, False, 'Credencial inválida.', event_id, setor_id=setor_id)
            return {
                'result': {
                    'event': 6,
                    'message': 'Credencial inválida.',
                    'user_id': user_id,
                    'user_name': user_name,
                    'user_image': False,
                    'portal_id': portal_id
                }
            }
        
        credential_id = cred['id']
        id_lote = cred['idLote']
        credencial = cred['codigoCredencial']

        # 4) O lote da credencial tem acesso a este setor?
        cursor.execute(
            "SELECT id FROM tblRelLoteSetor WHERE idLote = %s AND idSetor = %s AND status = 'T' LIMIT 1",
            (id_lote, setor_id)
        )
        rel = cursor.fetchone()
        if not rel:
            register_facial_access_attempt(user_id, leitor_id, False, 'Acesso não autorizado para este setor.', event_id, credential_id=credential_id, setor_id=setor_id, credential=credencial, idLote=id_lote)
            return {
                'result': {
                    'event': 6,
                    'message': 'Acesso não autorizado para este setor.',
                    'user_id': user_id,
                    'user_name': user_name,
                    'user_image': False,
                    'portal_id': portal_id
                }
            }

        # 5) O acesso está dentro de algum período válido do lote?
        cursor.execute(
            "SELECT dataInicio, dataTermino, horaInicio, horaTermino FROM tblLotePeriodo WHERE idLote = %s AND status = 'T'",
            (id_lote,)
        )
        periodos = cursor.fetchall()
        agora = datetime.now()
        acesso_permitido_no_periodo = False
        
        if not periodos: # Se não houver períodos definidos para o lote, o acesso pode ser livre
            acesso_permitido_no_periodo = False
        else:
            for p in periodos:
                # MySQL retorna TIME como timedelta, precisa converter para time
                hora_inicio = p['horaInicio']
                hora_termino = p['horaTermino']
                
                # Se for timedelta, converte para time
                if isinstance(hora_inicio, timedelta):
                    hora_inicio = (datetime.min + hora_inicio).time()
                if isinstance(hora_termino, timedelta):
                    hora_termino = (datetime.min + hora_termino).time()
                
                dt_ini = datetime.combine(p['dataInicio'], hora_inicio)
                dt_fim = datetime.combine(p['dataTermino'], hora_termino)
                
                if dt_ini <= agora <= dt_fim:
                    acesso_permitido_no_periodo = True
                    break

        if not acesso_permitido_no_periodo:
            register_facial_access_attempt(user_id, leitor_id, False, 'Fora do período de acesso.', event_id, credential_id=credential_id, setor_id=setor_id, credential=credencial, idLote=id_lote)
            return {
                'result': {
                    'event': 6,
                    'message': 'Fora do período de acesso.',
                    'user_id': user_id,
                    'user_name': user_name,
                    'user_image': False,
                    'portal_id': portal_id
                }
            }

        # 6) Acesso Concedido
        register_facial_access_attempt(user_id, leitor_id, True, 'Acesso concedido.', event_id, credential_id=credential_id, setor_id=setor_id, credential=credencial, idLote=id_lote)
        return {
            'result': {
                'event': 7,
                'user_id': user_id,
                'user_name': user_name,
                'user_image': False,
                'portal_id': portal_id,
                'actions': [
                    {'action': "sec_box", 'parameters': "id=65793, reason=1"}
                ]
            }
        }

    finally:
        cursor.close()
        conn.close()