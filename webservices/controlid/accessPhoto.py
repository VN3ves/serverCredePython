"""
Processamento de fotos de acesso enviadas pelos leitores faciais.
"""
import base64
import os
from datetime import datetime
from db import connection_pool
from config import SISTEMA_GERENCIAMENTO
from logging_config import get_logger

# Obtém o logger configurado para este módulo
logging = get_logger('AccessPhoto', arquivo_log='logAccessPhoto.log')


def handle_access_photo(
    device_id: str,
    time: str,
    portal_id: str,
    identifier_id: str,
    event: str,
    user_id: str,
    access_photo: str
):
    """
    Processa uma foto de acesso enviada pelo leitor facial.
    
    Args:
        device_id: ID do dispositivo que enviou a foto
        time: Timestamp do evento
        portal_id: ID do portal/porta
        identifier_id: ID do identificador
        event: Tipo de evento
        user_id: ID do usuário identificado
        access_photo: Foto em base64 (JPEG)
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        # Converte IDs para inteiros
        try:
            user_id_int = int(user_id) if user_id and user_id != '0' else 0
            device_id_int = int(device_id) if device_id else 0
            portal_id_int = int(portal_id) if portal_id else 0
            event_int = int(event) if event else 0
        except (ValueError, TypeError) as e:
            logging.error(f"Erro ao converter IDs: {str(e)}")
            return {'success': False, 'message': 'IDs inválidos'}
        
        logging.info(f"Recebendo foto de acesso - device_id: {device_id_int}, user_id: {user_id_int}, event: {event_int}")
        
        # Verifica se tem foto
        if not access_photo:
            logging.warning("Foto vazia recebida")
            return {'success': False, 'message': 'Foto vazia'}
        
        conn = connection_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Busca o leitor pelo device_id
            cursor.execute(
                "SELECT id, idEvento FROM tblLeitor WHERE deviceId = %s LIMIT 1",
                (device_id,)
            )
            leitor = cursor.fetchone()
            
            if not leitor:
                logging.warning(f"Leitor não encontrado: device_id={device_id}")
                return {'success': False, 'message': 'Leitor não encontrado'}
            
            leitor_id = leitor['id']
            event_id = leitor['idEvento']
            
            # Define o tipo de arquivo
            tipo_arquivo = 'ACESSO'  # Tipo específico para fotos de acesso
            
            # Cria o diretório para salvar a foto
            if user_id_int > 0:
                # Foto de usuário identificado
                diretorio = f"/midia/pessoas/{user_id_int}/acessos"
                id_referencia = user_id_int
                tipo_referencia = 'PESSOA'
            else:
                # Foto de acesso não identificado
                diretorio = f"/midia/acessos/nao_identificados"
                id_referencia = leitor_id
                tipo_referencia = 'LEITOR'
            
            caminho_completo = os.path.join(SISTEMA_GERENCIAMENTO, diretorio.lstrip('/'))
            os.makedirs(caminho_completo, exist_ok=True)
            
            # Gera nome único para o arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            nome_arquivo = f"acesso_{timestamp}.jpg"
            caminho_arquivo = os.path.join(caminho_completo, nome_arquivo)
            path_local = f"{diretorio}/{nome_arquivo}"
            
            # Decodifica e salva a foto
            try:
                foto_bytes = base64.b64decode(access_photo)
                with open(caminho_arquivo, 'wb') as f:
                    f.write(foto_bytes)
                logging.info(f"Foto salva em: {path_local}")
            except Exception as e:
                logging.error(f"Erro ao salvar foto: {str(e)}")
                return {'success': False, 'message': 'Erro ao salvar foto'}
            
            # Registra no banco de dados (tblArquivo)
            cursor.execute("""
                INSERT INTO tblArquivo
                    (idReferencia, tipoReferencia, tipoArquivo, 
                     pathLocal, dataCadastro)
                VALUES (%s, %s, %s, %s, NOW())
            """, (
                id_referencia,
                tipo_referencia,
                tipo_arquivo,
                path_local
            ))
            
            arquivo_id = cursor.lastrowid
            
            # Busca a entrada mais recente deste usuário/leitor para relacionar
            if user_id_int > 0:
                cursor.execute("""
                    SELECT id FROM tblEntradas
                    WHERE idPessoa = %s AND idLeitor = %s
                    ORDER BY dataTentativa DESC
                    LIMIT 1
                """, (user_id_int, leitor_id))
            else:
                cursor.execute("""
                    SELECT id FROM tblEntradas
                    WHERE idLeitor = %s AND idPessoa IS NULL
                    ORDER BY dataTentativa DESC
                    LIMIT 1
                """, (leitor_id,))
            
            entrada = cursor.fetchone()
            
            # Se encontrou uma entrada, atualiza com o ID do arquivo
            if entrada:
                cursor.execute("""
                    UPDATE tblEntradas
                    SET idArquivo = %s
                    WHERE id = %s
                """, (arquivo_id, entrada['id']))
                logging.info(f"Foto relacionada com entrada ID: {entrada['id']}")
            else:
                logging.warning(f"Nenhuma entrada encontrada para relacionar a foto (user_id: {user_id_int}, leitor_id: {leitor_id})")
            
            conn.commit()
            
            logging.info(f"Foto de acesso processada com sucesso - arquivo_id: {arquivo_id}")
            return {
                'success': True,
                'message': 'Foto recebida e processada com sucesso',
                'arquivo_id': arquivo_id
            }
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logging.error(f"Erro ao processar foto de acesso: {str(e)}", exc_info=True)
        return {'success': False, 'message': f'Erro: {str(e)}'}

