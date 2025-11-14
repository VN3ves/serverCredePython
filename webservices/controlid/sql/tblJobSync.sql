-- Tabela de Jobs para Sincronização de Imagens
-- Similar ao sistema de jobs do Laravel

CREATE TABLE IF NOT EXISTS `tblJobSync` (
  `id` int NOT NULL AUTO_INCREMENT,
  `idEvento` int NOT NULL,
  `idPessoa` int NOT NULL COMMENT 'ID da pessoa que teve a foto cadastrada',
  `idArquivo` int NOT NULL COMMENT 'ID do arquivo/foto a ser sincronizado',
  `tentativas` tinyint NOT NULL DEFAULT '0' COMMENT 'Número de tentativas realizadas',
  `maxTentativas` tinyint NOT NULL DEFAULT '3' COMMENT 'Máximo de tentativas permitidas',
  `status` enum('PENDENTE','PROCESSANDO','CONCLUIDO','FALHA') NOT NULL DEFAULT 'PENDENTE',
  `payload` json DEFAULT NULL COMMENT 'Dados adicionais do job em JSON',
  `mensagemErro` text COMMENT 'Última mensagem de erro, se houver',
  `dataAgendamento` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Quando o job foi criado',
  `dataInicio` timestamp NULL DEFAULT NULL COMMENT 'Quando começou a processar',
  `dataConclusao` timestamp NULL DEFAULT NULL COMMENT 'Quando foi concluído',
  PRIMARY KEY (`id`),
  KEY `idx_pessoa` (`idPessoa`),
  KEY `idx_arquivo` (`idArquivo`),
  KEY `idx_evento` (`idEvento`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Fila de jobs para sincronização de imagens com leitores faciais';

-- Índice composto para buscar jobs prontos para processar
CREATE INDEX idx_processar_jobs ON tblJobSync (status, dataAgendamento, tentativas);

