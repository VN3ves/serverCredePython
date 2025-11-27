from .DBConfig import connection_pool, conectarBancoEvento
from .accessAttempt import register_facial_access_attempt
from .funcoes import updateLeitorSession, updateLeitorDeviceId, findLeitores, findLeitoresParaConfigurar, getEventoBanco, marcarLeitorConfigurado, updateLeitorServerId, updateLeitor