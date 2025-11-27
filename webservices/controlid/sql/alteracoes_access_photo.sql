-- Alterações necessárias para suporte a fotos de acesso

-- 1. Adicionar campo idArquivo na tabela tblEntradas (se não existir)
ALTER TABLE `tblEntradas` 
ADD COLUMN `idArquivo` INT NULL AFTER `mensagem`,
ADD INDEX `idx_idArquivo` (`idArquivo`);

ALTER TABLE `tblEntradas` 
ADD COLUMN `idLote` INT NULL AFTER `idPessoa`;

-- 2. Modificar enum de tipoArquivo para incluir 'ACESSO' (se não existir)
ALTER TABLE `tblArquivo` 
MODIFY COLUMN `tipoArquivo` ENUM('AVATAR','DOCUMENTO','LOGO','BANNER','ACESSO','OUTROS') 
CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL;

-- 3. Adicionar chave estrangeira (opcional, para integridade referencial)
-- ALTER TABLE `tblEntradas` 
-- ADD CONSTRAINT `fk_entrada_arquivo` 
-- FOREIGN KEY (`idArquivo`) REFERENCES `tblArquivo`(`id`) 
-- ON DELETE SET NULL ON UPDATE CASCADE;

