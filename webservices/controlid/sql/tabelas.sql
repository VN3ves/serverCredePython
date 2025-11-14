-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 192.168.3.90:3306
-- Tempo de geração: 12-Nov-2025 às 00:27
-- Versão do servidor: 8.0.43-0ubuntu0.24.04.1
-- versão do PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `tcc_crede`
--

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblArquivo`
--

CREATE TABLE `tblArquivo` (
  `id` int NOT NULL,
  `idReferencia` int NOT NULL,
  `tipoReferencia` enum('PESSOA','EMPRESA','EVENTO') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `pathLocal` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pathNuvem` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `observacao` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tipoArquivo` enum('AVATAR','DOCUMENTO','LOGO','BANNER','OUTROS') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `arqSincronizadaNuvem` tinyint(1) NOT NULL DEFAULT '0',
  `arqSincronizadaLeitores` tinyint(1) NOT NULL DEFAULT '0',
  `deviceId` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataAtualizacao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblCredencial`
--

CREATE TABLE `tblCredencial` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idLote` char(36) NOT NULL,
  `idPessoa` char(36) DEFAULT NULL,
  `idUsuarioCadastro` int DEFAULT NULL,
  `docPessoa` varchar(255) DEFAULT NULL,
  `nomeCredencial` varchar(100) NOT NULL,
  `codigoCredencial` text NOT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `detalhes` varchar(255) DEFAULT NULL,
  `status` enum('T','F') DEFAULT 'T',
  `impresso` enum('T','F') DEFAULT 'F',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataImpressao` timestamp NULL DEFAULT NULL,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblCredencialPeriodo`
--

CREATE TABLE `tblCredencialPeriodo` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idCredencial` char(36) NOT NULL,
  `dataInicio` date NOT NULL,
  `dataTermino` date NOT NULL,
  `horaInicio` time NOT NULL,
  `horaTermino` time NOT NULL,
  `status` enum('T','F') DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblDocumento`
--

CREATE TABLE `tblDocumento` (
  `id` int NOT NULL,
  `idPessoa` int DEFAULT NULL,
  `tipo` enum('RG','CPF','Passaporte','Outros','CNH','CNPJ','IE') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `titulo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `documento` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `detalhes` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEmail`
--

CREATE TABLE `tblEmail` (
  `id` int NOT NULL,
  `idPessoa` int DEFAULT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEndereco`
--

CREATE TABLE `tblEndereco` (
  `id` int NOT NULL,
  `idPessoa` int DEFAULT NULL,
  `idEmpresa` int DEFAULT NULL,
  `titulo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cep` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `logradouro` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `numero` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `complemento` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `zona` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bairro` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cidade` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `estado` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEntradas`
--

CREATE TABLE `tblEntradas` (
  `id` int NOT NULL,
  `idEvento` int DEFAULT NULL,
  `idPessoa` char(36) DEFAULT NULL,
  `idCredencial` char(36) DEFAULT NULL,
  `idSetor` char(36) DEFAULT NULL,
  `idLeitor` char(36) DEFAULT NULL,
  `credencial` text,
  `tipoEntrada` enum('ENTRADA','SAIDA') NOT NULL DEFAULT 'ENTRADA',
  `dataTentativa` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `permitida` enum('T','F') DEFAULT 'F',
  `mensagem` varchar(250) DEFAULT NULL,
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEvento`
--

CREATE TABLE `tblEvento` (
  `id` int NOT NULL,
  `idCategoria` int NOT NULL,
  `idLocal` int DEFAULT NULL,
  `nomeEvento` varchar(100) NOT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `dataInicio` date DEFAULT NULL,
  `dataFim` date DEFAULT NULL,
  `status` enum('T','F') DEFAULT 'F',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEventoCategoria`
--

CREATE TABLE `tblEventoCategoria` (
  `id` int NOT NULL,
  `nomeCategoria` varchar(100) NOT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `status` enum('T','F') DEFAULT 'F',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEventoComponentes`
--

CREATE TABLE `tblEventoComponentes` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `qtdSetores` int DEFAULT '0',
  `usaLeitorFacial` enum('S','N') DEFAULT 'N',
  `qtdLeitoresFaciais` int DEFAULT '0',
  `credenciaisImpressas` enum('S','N') DEFAULT 'N',
  `qtdLotesCredenciais` int DEFAULT '0',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `marcaLeitor` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblEventoLocal`
--

CREATE TABLE `tblEventoLocal` (
  `id` int NOT NULL,
  `nomeOficial` varchar(255) DEFAULT NULL,
  `cep` varchar(10) DEFAULT NULL,
  `logradouro` varchar(255) DEFAULT NULL,
  `numero` varchar(10) DEFAULT NULL,
  `bairro` varchar(100) DEFAULT NULL,
  `cidade` varchar(100) DEFAULT NULL,
  `estado` varchar(100) DEFAULT NULL,
  `complemento` varchar(255) DEFAULT NULL,
  `latitude` varchar(50) DEFAULT NULL,
  `longitude` varchar(50) DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblHistorico`
--

CREATE TABLE `tblHistorico` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idReferencia` char(36) DEFAULT NULL,
  `tipoReferencia` enum('EVENTO','SETOR','TERMINAL','LEITOR','CREDENCIAL','LOTE') NOT NULL,
  `idUsuario` char(36) DEFAULT NULL,
  `idServidor` int DEFAULT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `sql` text,
  `tipo` enum('CADASTRO','EDICAO','DESATIVACAO','ATIVACAO','APROVACAO','REPROVACAO','CANCELAMENTO','LIBERACAO','BLOQUEIO') NOT NULL,
  `ipUsuario` varchar(45) DEFAULT NULL,
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblHistoricoToken`
--

CREATE TABLE `tblHistoricoToken` (
  `id` int NOT NULL,
  `idToken` int NOT NULL,
  `acao` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `observacao` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dataUso` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `idUsuario` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblLeitor`
--

CREATE TABLE `tblLeitor` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idSetor` char(36) DEFAULT NULL,
  `nomeLeitor` varchar(100) DEFAULT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `ip` varchar(39) NOT NULL,
  `usuario` varchar(100) DEFAULT NULL,
  `senha` varchar(100) DEFAULT NULL,
  `deviceId` varchar(100) DEFAULT NULL,
  `serverId` varchar(100) DEFAULT NULL,
  `serverUrl` varchar(100) DEFAULT NULL,
  `session` varchar(100) DEFAULT NULL,
  `condicao` varchar(5) NOT NULL DEFAULT 'OFF',
  `status` enum('T','F') DEFAULT 'T',
  `configurado` enum('T','F') DEFAULT 'F',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblLeitorFoto`
--

CREATE TABLE `tblLeitorFoto` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idLeitor` char(36) NOT NULL,
  `idArquivo` char(36) NOT NULL,
  `status` int DEFAULT '1',
  `mensagem` varchar(255) DEFAULT NULL,
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblLog`
--

CREATE TABLE `tblLog` (
  `id` int NOT NULL,
  `idUsuario` int DEFAULT '0',
  `stringSQL` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `acao` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `modulo` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ip` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblLote`
--

CREATE TABLE `tblLote` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `nomeLote` varchar(100) NOT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `qtdTempoEntreLeitura` int NOT NULL DEFAULT '5',
  `status` enum('T','F') DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblLotePeriodo`
--

CREATE TABLE `tblLotePeriodo` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idLote` char(36) NOT NULL,
  `dataInicio` date NOT NULL,
  `dataTermino` date NOT NULL,
  `horaInicio` time NOT NULL,
  `horaTermino` time NOT NULL,
  `status` enum('T','F') DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblPermissao`
--

CREATE TABLE `tblPermissao` (
  `id` int NOT NULL,
  `permissao` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblPessoa`
--

CREATE TABLE `tblPessoa` (
  `id` int NOT NULL,
  `nome` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sobrenome` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `apelido` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `genero` enum('Masculino','Feminino','Outros') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `dataNascimento` date DEFAULT NULL,
  `observacoes` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblRelCredencialSetor`
--

CREATE TABLE `tblRelCredencialSetor` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idCredencial` char(36) NOT NULL,
  `idSetor` char(36) NOT NULL,
  `permiteSaida` tinyint(1) DEFAULT '0',
  `permiteReentrada` tinyint(1) DEFAULT '0',
  `tipoReentrada` int DEFAULT NULL,
  `status` enum('T','F') DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblRelLoteSetor`
--

CREATE TABLE `tblRelLoteSetor` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `idLote` char(36) NOT NULL,
  `idSetor` char(36) NOT NULL,
  `permiteSaida` tinyint(1) DEFAULT '0',
  `permiteReentrada` tinyint(1) DEFAULT '0',
  `tipoReentrada` int DEFAULT NULL,
  `status` enum('T','F') DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblSetor`
--

CREATE TABLE `tblSetor` (
  `id` int NOT NULL,
  `idEvento` int NOT NULL,
  `nomeSetor` varchar(100) NOT NULL,
  `observacao` varchar(255) DEFAULT NULL,
  `status` enum('T','F') DEFAULT 'T',
  `dataCadastro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblTelefone`
--

CREATE TABLE `tblTelefone` (
  `id` int NOT NULL,
  `idPessoa` int DEFAULT NULL,
  `telefone` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tipo` enum('Fixo','Celular') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblToken`
--

CREATE TABLE `tblToken` (
  `id` int NOT NULL,
  `idEmpresa` int DEFAULT NULL,
  `token` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `idParceiro` int DEFAULT NULL,
  `dataCadastro` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `type` enum('CADASTRO','ACESSO') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'CADASTRO',
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'T',
  `deletado` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `tblUsuario`
--

CREATE TABLE `tblUsuario` (
  `id` int NOT NULL,
  `idPessoa` int NOT NULL,
  `idPermissao` int NOT NULL,
  `senha` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sessionID` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `token` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('T','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'F',
  `dataCriacao` datetime DEFAULT CURRENT_TIMESTAMP,
  `dataEdicao` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `usuario` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tabelas despejadas
--

--
-- Índices para tabela `tblArquivo`
--
ALTER TABLE `tblArquivo`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblCredencial`
--
ALTER TABLE `tblCredencial`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblCredencialPeriodo`
--
ALTER TABLE `tblCredencialPeriodo`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblDocumento`
--
ALTER TABLE `tblDocumento`
  ADD PRIMARY KEY (`id`) USING BTREE,
  ADD UNIQUE KEY `id_UNIQUE` (`id`) USING BTREE,
  ADD UNIQUE KEY `documento` (`documento`) USING BTREE,
  ADD KEY `fk_tblDocumento_tblPessoa1_idx` (`idPessoa`) USING BTREE;

--
-- Índices para tabela `tblEmail`
--
ALTER TABLE `tblEmail`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_UNIQUE` (`id`);

--
-- Índices para tabela `tblEndereco`
--
ALTER TABLE `tblEndereco`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_UNIQUE` (`id`),
  ADD KEY `fk_tblEndereco_tblPessoa1_idx` (`idPessoa`);

--
-- Índices para tabela `tblEntradas`
--
ALTER TABLE `tblEntradas`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblEvento`
--
ALTER TABLE `tblEvento`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblEventoCategoria`
--
ALTER TABLE `tblEventoCategoria`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblEventoComponentes`
--
ALTER TABLE `tblEventoComponentes`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblEventoLocal`
--
ALTER TABLE `tblEventoLocal`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblHistorico`
--
ALTER TABLE `tblHistorico`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblHistoricoToken`
--
ALTER TABLE `tblHistoricoToken`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblLeitor`
--
ALTER TABLE `tblLeitor`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblLeitorFoto`
--
ALTER TABLE `tblLeitorFoto`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblLog`
--
ALTER TABLE `tblLog`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_UNIQUE` (`id`),
  ADD KEY `fk_tblLog_tblUsuario1_idx` (`idUsuario`);

--
-- Índices para tabela `tblLote`
--
ALTER TABLE `tblLote`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblLotePeriodo`
--
ALTER TABLE `tblLotePeriodo`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblPermissao`
--
ALTER TABLE `tblPermissao`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `idtblPermissao_UNIQUE` (`id`);

--
-- Índices para tabela `tblPessoa`
--
ALTER TABLE `tblPessoa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_UNIQUE` (`id`);

--
-- Índices para tabela `tblRelCredencialSetor`
--
ALTER TABLE `tblRelCredencialSetor`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblRelLoteSetor`
--
ALTER TABLE `tblRelLoteSetor`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblSetor`
--
ALTER TABLE `tblSetor`
  ADD PRIMARY KEY (`id`);

--
-- Índices para tabela `tblTelefone`
--
ALTER TABLE `tblTelefone`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_UNIQUE` (`id`),
  ADD KEY `fk_tblTelefone_tblPessoa_idx` (`idPessoa`);

--
-- Índices para tabela `tblToken`
--
ALTER TABLE `tblToken`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `token` (`token`);

--
-- Índices para tabela `tblUsuario`
--
ALTER TABLE `tblUsuario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_UNIQUE` (`id`),
  ADD UNIQUE KEY `idPessoa` (`idPessoa`),
  ADD KEY `fk_tblUsuario_tblPessoa1_idx` (`idPessoa`),
  ADD KEY `fk_tblUsuario_tblPermissao1_idx` (`idPermissao`);

--
-- AUTO_INCREMENT de tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `tblArquivo`
--
ALTER TABLE `tblArquivo`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblCredencial`
--
ALTER TABLE `tblCredencial`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblCredencialPeriodo`
--
ALTER TABLE `tblCredencialPeriodo`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblDocumento`
--
ALTER TABLE `tblDocumento`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEmail`
--
ALTER TABLE `tblEmail`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEndereco`
--
ALTER TABLE `tblEndereco`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEntradas`
--
ALTER TABLE `tblEntradas`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEvento`
--
ALTER TABLE `tblEvento`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEventoCategoria`
--
ALTER TABLE `tblEventoCategoria`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEventoComponentes`
--
ALTER TABLE `tblEventoComponentes`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblEventoLocal`
--
ALTER TABLE `tblEventoLocal`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblHistorico`
--
ALTER TABLE `tblHistorico`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblHistoricoToken`
--
ALTER TABLE `tblHistoricoToken`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblLeitor`
--
ALTER TABLE `tblLeitor`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblLeitorFoto`
--
ALTER TABLE `tblLeitorFoto`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblLog`
--
ALTER TABLE `tblLog`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblLote`
--
ALTER TABLE `tblLote`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblLotePeriodo`
--
ALTER TABLE `tblLotePeriodo`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblPermissao`
--
ALTER TABLE `tblPermissao`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblPessoa`
--
ALTER TABLE `tblPessoa`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblRelCredencialSetor`
--
ALTER TABLE `tblRelCredencialSetor`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblRelLoteSetor`
--
ALTER TABLE `tblRelLoteSetor`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblSetor`
--
ALTER TABLE `tblSetor`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblTelefone`
--
ALTER TABLE `tblTelefone`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblToken`
--
ALTER TABLE `tblToken`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `tblUsuario`
--
ALTER TABLE `tblUsuario`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
