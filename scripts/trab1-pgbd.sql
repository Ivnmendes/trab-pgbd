create database if not exists bdedica_wf;
use bdedica_wf;

-- 1. CRIAÇÃO DAS TABELAS -- 
-- 1.1. USUÁRIO -- 
create table if not exists usuario (
id bigint primary key auto_increment,
username varchar(50) not null,
nome varchar(100) not null,
cargo enum('ORIENTADOR', 'COORDENADOR', 'JIJ') not null,
senha varchar(255) not null);

-- 1.2. TEMPLATE_PROCESSO -- 
create table if not exists template_processo (
id bigint primary key auto_increment,
nome varchar(100) not null,
descricao tinytext not null );

-- 1.3. PROCESSO -- 
create table if not exists processo (
id bigint primary key auto_increment,
id_template bigint not null,
id_usuario bigint not null,
status_proc enum('PENDENTE', 'CONCLUIDO') default 'PENDENTE' not null,
data_inicio datetime default NOW() not null,
foreign key (id_template) references template_processo(id),
foreign key (id_usuario) references usuario(id));

-- 1.4. ETAPA -- 
create table if not exists etapa (
id bigint primary key auto_increment,
id_template bigint not null,
nome varchar(100) not null,
ordem int not null,
responsavel enum('ORIENTADOR', 'COORDENADOR', 'JIJ'),
foreign key (id_template) references template_processo(id)
);

-- 1.5. FLUXO DE EXECUÇÃO DE ETAPAS --
create table if not exists fluxo_execucao ( 
id bigint primary key auto_increment,
id_origem bigint not null,
id_destino bigint not null,
foreign key (id_origem) references etapa(id),
foreign key (id_destino) references etapa(id));

-- 1.6. ETAPAS EM EXECUÇÃO --
create table if not exists execucao_etapa (
id bigint primary key auto_increment,
id_processo bigint not null,
id_etapa bigint not null,
id_usuario bigint not null,
observacoes text not null,
data_inicio datetime default now() not null,
data_fim datetime,
status enum('PENDENTE', 'CONCLUIDO') default 'PENDENTE' not null,
foreign key (id_processo) references processo(id),
foreign key (id_etapa) references etapa(id),
foreign key (id_usuario) references usuario(id)
);

-- 1.7. MODELO DE CAMPO PARA CADA ETAPA -- 
create table if not exists modelo_campo (
id bigint primary key auto_increment,
id_etapa bigint not null,
nome_campo varchar(100) not null,
tipo enum('TEXTO', 'NUMERO', 'DATA', 'ARQUIVO') not null,
obrigatorio boolean default false,
foreign key (id_etapa) references etapa(id)
);

-- 1.8. CAMPO -- 
create table if not exists campo (
id bigint primary key auto_increment,
id_modelo bigint not null,
dados text);


-- 2. CRIANDO USUÁRIOS E PERMISSÕES

-- 2.1. USUÁRIO ORIENTADOR --
DROP USER if exists 'orientador'@localhost;
CREATE USER 'orientador'@localhost IDENTIFIED BY '1234';
GRANT SELECT, INSERT, UPDATE ON bdedica.relatorio TO 'orientador'@localhost;
GRANT SELECT ON bdedica.adolescente TO 'orientador'@localhost;
GRANT SELECT (id, nome, cargo) ON bdedica.usuario TO 'orientador'@localhost;
GRANT SELECT ON bdedica.mse TO 'orientador'@localhost;
FLUSH PRIVILEGES;

-- 2.2. USUÁRIO COORDENADOR --
DROP USER if exists 'coordenador'@localhost;
CREATE USER 'coordenador'@localhost IDENTIFIED BY '4321';
GRANT SELECT, UPDATE, DELETE ON bdedica.* TO 'coordenador'@localhost;
GRANT INSERT ON bdedica.usuario TO 'coordenador'@localhost;
GRANT INSERT ON bdedica.mse TO 'coordenador'@localhost;
GRANT INSERT ON bdedica.adolescente TO 'coordenador'@localhost;
FLUSH PRIVILEGES;

-- 2.3. USUÁRIO JIJ --
DROP USER if exists 'jij'@localhost;
CREATE USER 'jij'@localhost IDENTIFIED BY '2143';
GRANT SELECT, UPDATE on bdedica.relatorio TO 'jij'@localhost;
GRANT SELECT on bdedica.adolescente TO 'jij'@localhost;
GRANT SELECT, UPDATE on bdedica.mse TO 'jij'@localhost;
GRANT SELECT (id, nome, cargo) ON bdedica.usuario TO 'jij'@localhost;
FLUSH PRIVILEGES;

-- 3. FUNCTIONS --
-- 3.1. VERIFICA SE O STATUS DO RELATÓRIO ESTÁ CORRETO --
DELIMITER $$
CREATE FUNCTION verifica_status(status_atual varchar(50), status_desejado varchar(50))
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    IF status_atual = status_desejado THEN
		RETURN TRUE;
	ELSE
		RETURN FALSE;
	END IF;
END 
$$
DELIMITER ;
    
-- 4. TRIGGERS --
-- 4.1. GARANTINDO QUE O USUÁRIO INSERIDO EM MSE É UM ORIENTADOR E QUE SEMANAS RESTANTES = SEMANAS TOTAIS -- 
DELIMITER $$
CREATE TRIGGER insertMse
	BEFORE INSERT ON mse
    FOR EACH ROW
    BEGIN
    DECLARE cargo1 varchar(50);
    SELECT cargo INTO cargo1 FROM usuario
    WHERE id = NEW.id_orientador;
    IF cargo1 != 'ORIENTADOR' THEN
		SIGNAL SQLSTATE'45000'
		SET MESSAGE_TEXT = 'Usuário inválido; usuário responsável deve ser um ORIENTADOR';
	END IF;
    IF NEW.semanas_restantes != NEW.semanas_totais THEN
		SIGNAL SQLSTATE'45001'
		SET MESSAGE_TEXT = 'O número de semanas restantes deve ser igual ao número de semanas totais';
	END IF;
END
$$ 
DELIMITER ;

-- 4.2. GARANTINDO QUE O STATUS DO RELATÓRIO ESTEJA 'PENDENTE' QUANDO É CRIADO -- 
DELIMITER $$
CREATE TRIGGER insertRel
	BEFORE INSERT ON relatorio
    FOR EACH ROW
    BEGIN
    DECLARE p_status boolean;
    SET p_status = verifica_status(NEW.status_rel,'PENDENTE');
    
    IF p_status = FALSE THEN
		SIGNAL SQLSTATE'45000'
		SET MESSAGE_TEXT = 'O status inicial de um relatório deve ser PENDENTE';
	END IF;
END
$$ 
DELIMITER ;

-- 4.3. VERIFICAÇÃO DAS PERMISSÕES DE MUDANÇA DE STATUS E CORREÇÃO DO CAMPO OBSERVAÇÕES --
DELIMITER $$

CREATE TRIGGER updateCorrecao
BEFORE UPDATE ON relatorio
FOR EACH ROW
BEGIN
    DECLARE usuario_db VARCHAR(50);
    DECLARE status_atual VARCHAR(50);
    SET usuario_db = SESSION_USER();
    
    SELECT status_rel INTO status_atual FROM relatorio
    WHERE id = NEW.id;

    IF NEW.status_rel = 'AGUARDA_CORRECOES' THEN
        IF NEW.observacoes IS NULL OR NEW.observacoes = '' THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'O campo Observações deve ser preenchido para enviar para Correção.';
        END IF;
        IF usuario_db NOT LIKE 'coordenador@%' THEN
            SIGNAL SQLSTATE '45001'
            SET MESSAGE_TEXT = 'Somente o Coordenador pode encaminhar para Correção.';
        END IF;

    ELSEIF NEW.status_rel = 'PENDENTE' THEN
        IF usuario_db NOT LIKE 'orientador@%' THEN
            SIGNAL SQLSTATE '45002'
            SET MESSAGE_TEXT = 'Somente o Orientador pode mudar o status para Pendente.';
        END IF;

    ELSEIF NEW.status_rel = 'ENVIADO' THEN
        SET NEW.observacoes = NULL;
        IF usuario_db NOT LIKE 'coordenador@%' THEN
            SIGNAL SQLSTATE '45003'
            SET MESSAGE_TEXT = 'Somente o Coordenador pode mudar o status para Enviado.';
        END IF;

    ELSEIF NEW.status_rel = 'CONCLUIDO' THEN
        IF usuario_db NOT LIKE 'jij@%' THEN
            SIGNAL SQLSTATE '45004'
            SET MESSAGE_TEXT = 'Somente o representante do JIJ pode definir o relatório como Concluído.';
        END IF;
        IF status_atual != 'ENVIADO' THEN
			SIGNAL SQLSTATE '45005'
            SET MESSAGE_TEXT = 'Um relatório só pode ser concluído após envio pelo Coordenador';
		END IF;
    END IF;
END$$

DELIMITER ;

-- 4.4. ATUALIZAÇÃO DAS SEMANAS RESTANTES DA MSE -- 
DELIMITER $$

CREATE TRIGGER updateMse
AFTER UPDATE ON relatorio
FOR EACH ROW
BEGIN
	DECLARE num_semanas int;
    DECLARE restantes int;
    IF NEW.status_rel = 'CONCLUIDO' THEN
		SELECT presencas into num_semanas from relatorio
        WHERE id = NEW.id;
        SELECT semanas_restantes into restantes from mse
        WHERE id = NEW.id_mse;
        UPDATE mse SET semanas_restantes = restantes - num_semanas
        WHERE id = NEW.id_mse;
        
        IF restantes - num_semanas <= 0 THEN
			UPDATE mse SET status_mse = 'CONCLUIDA'
            WHERE id = NEW.id_mse;
		END IF;
        
	END IF;
END$$

DELIMITER ;

-- AUXILIARES -- 