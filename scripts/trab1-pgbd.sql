create database if not exists bdedica;
use bdedica;

-- 1. CRIAÇÃO DAS TABELAS -- 
-- 1.1. ADOLESCENTE -- 
create table if not exists adolescente (
id int primary key auto_increment,
nome varchar(100) not null);

-- 1.2. USUÁRIO -- 
create table if not exists usuario (
id int primary key auto_increment,
username varchar(50) not null,
nome varchar(100) not null,
cargo enum('ORIENTADOR', 'COORDENADOR', 'JIJ') not null,
senha varchar(255) not null);

-- 1.3. MSE -- 
create table if not exists mse (
id int primary key auto_increment,
id_adolescente int not null,
id_orientador int not null,
semanas_totais int not null,
semanas_restantes int not null,
status_mse enum('EM_ANDAMENTO', 'CONCLUIDA'),
foreign key (id_adolescente) references adolescente(id),
foreign key (id_orientador) references usuario(id));

-- 1.4. RELATÓRIO -- 
create table if not exists relatorio (
id int primary key auto_increment,
id_mse int not null,
mes varchar(50) not null,
ano int not null,
presencas int not null,
faltas int not null,
relato text not null,
observacoes tinytext null,
status_rel enum('PENDENTE', 'AGUARDA_CORRECOES', 'ENVIADO', 'CONCLUIDO'),
FOREIGN KEY (id_mse) REFERENCES mse(id));

-- 2. CRIANDO USUÁRIOS E PERMISSÕES

-- 2.1. USUÁRIO ORIENTADOR --
DROP USER if exists 'orientador'@localhost;
CREATE USER 'orientador'@localhost IDENTIFIED WITH mysql_native_password BY '1234';
GRANT SELECT, INSERT, UPDATE ON bdedica.relatorio TO 'orientador'@localhost;
GRANT SELECT ON bdedica.adolescente TO 'orientador'@localhost;
GRANT SELECT (id, nome, cargo) ON bdedica.usuario TO 'orientador'@localhost;
GRANT SELECT ON bdedica.mse TO 'orientador'@localhost;
FLUSH PRIVILEGES;

-- 2.2. USUÁRIO COORDENADOR --
DROP USER if exists 'coordenador'@localhost;
CREATE USER 'coordenador'@localhost IDENTIFIED WITH mysql_native_password BY '4321';
GRANT SELECT, UPDATE, DELETE ON bdedica.* TO 'coordenador'@localhost;
GRANT INSERT ON bdedica.usuario TO 'coordenador'@localhost;
GRANT INSERT ON bdedica.mse TO 'coordenador'@localhost;
GRANT INSERT ON bdedica.adolescente TO 'coordenador'@localhost;
FLUSH PRIVILEGES;

-- 2.3. USUÁRIO JIJ --
DROP USER if exists 'jij'@localhost;
CREATE USER 'jij'@localhost IDENTIFIED WITH mysql_native_password BY '2143';
GRANT SELECT, UPDATE on bdedica.relatorio TO 'jij'@localhost;
GRANT SELECT on bdedica.adolescente TO 'jij'@localhost;
GRANT SELECT, UPDATE on bdedica.mse TO 'jij'@localhost;
GRANT SELECT (id, nome, cargo) ON bdedica.usuario TO 'jij'@localhost;
FLUSH PRIVILEGES;

-- 2.4. USUÁRIO AUTENTICAÇÂO --
DROP USER if exists 'autenticacao'@localhost;
CREATE USER 'autenticacao'@localhost IDENTIFIED WITH mysql_native_password BY '4312';
GRANT SELECT ON bdedica.usuario TO 'autenticacao'@localhost;
FLUSH PRIVILEGES;

-- 2.5. USUÁRIO ADMINISTRADOR --
DROP USER if exists 'admin'@localhost;
CREATE USER 'admin'@localhost IDENTIFIED WITH mysql_native_password BY 'django_admin_pass';
GRANT ALL PRIVILEGES ON bdedica.* TO 'admin'@localhost;
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
