import mysql.connector
from mysql.connector import pooling

# Ajuste estes valores conforme seu ambiente:
DB_CONFIG = {
    "host":     "192.168.3.90",
    "port":     3306,
    "user":     "crede",
    "password": "crede@123",
    "database": "tcc_crede"
}

# Cria um pool de conexões reutilizável
connection_pool = pooling.MySQLConnectionPool(
    pool_name     = "mypool",
    pool_size     = 5,
    pool_reset_session = True,
    **DB_CONFIG
)

def conectarBancoCrede():
    import mysql.connector
    return mysql.connector.connect(**DB_CONFIG)

def conectarBancoEvento():
    """
    Conecta ao banco de dados do evento.
    Por enquanto, retorna a mesma conexão do banco Crede.
    """
    import mysql.connector
    return mysql.connector.connect(**DB_CONFIG)