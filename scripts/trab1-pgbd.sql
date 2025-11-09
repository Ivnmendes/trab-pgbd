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
campo_anexo boolean default false,
responsavel enum('ORIENTADOR', 'COORDENADOR', 'JIJ') not null,
foreign key (id_template) references template_processo(id)
);

-- 1.5. FLUXO DE EXECUÇÃO DE ETAPAS --
create table if not exists fluxo_execucao ( 
id bigint primary key auto_increment,
id_origem bigint not null,
id_destino bigint not null,
unique (id_origem, id_destino),
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
anexo varchar(255),
status_exec enum('PENDENTE', 'CONCLUIDO') default 'PENDENTE' not null,
foreign key (id_processo) references processo(id),
foreign key (id_etapa) references etapa(id),
foreign key (id_usuario) references usuario(id)
);

-- 2. FUNCTIONS 
-- 2.1. Verifica se a etapa sendo inserida precisa de anexo -- 
DELIMITER $$
CREATE FUNCTION anexoObrigatorio(idEtapa bigint)
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
	DECLARE anexo_obrigatorio boolean default false;
    
    select campo_anexo into anexo_obrigatorio
    from etapa
    where id = idEtapa
    limit 1;
    
    return anexo_obrigatorio;
END $$

DELIMITER ;

-- 3. PROCEDURES -- 
-- 3.1. VERIFICA SE O FLUXO DE EXECUÇÃO ESTÁ OCORRENDO --
DELIMITER $$
CREATE PROCEDURE validacaoEtapas(IN novo_id_processo bigint, in novo_id_etapa bigint, in novo_id_usuario bigint, 
in novo_observacoes text, in novo_anexo varchar(255))
	BEGIN
		DECLARE id_ultima_etapa bigint;
        DECLARE id_etapa_final bigint;
        DECLARE precisa_anexo boolean;
        
        -- vai selecionar a última etapa do processo inserida no banco --
        select id_etapa into id_ultima_etapa from execucao_etapa
        where id_processo = novo_id_processo
        and data_inicio = ( select max(data_inicio) from execucao_etapa
								where id_processo = novo_id_processo);
                                
		-- descobre qual a etapa final do processo -- 
        select e.id into id_etapa_final 
		from etapa e join fluxo_execucao f on f.id_origem = e.id
        where f.id_origem = f.id_destino
        limit 1;
        
        -- verifica se precisa de anexo --
        SET precisa_anexo = anexoObrigatorio(novo_id_etapa);
		
		controle_insert: BEGIN
		-- se é nulo, é a primeira etapa e não precisa validar a sequência -- 
		IF id_ultima_etapa IS NOT NULL THEN 
			-- valida se o fluxo é válido -- 
			IF NOT EXISTS (select 1 from fluxo_execucao
									where id_origem = id_ultima_etapa 
                                    and id_destino = novo_id_etapa) THEN
				SIGNAL SQLSTATE '45000'
				SET MESSAGE_TEXT = 'Fluxo inválido: etapa não pode ser executada';
			END IF;
				-- confere a obrigatoriedade do anexo --
                IF precisa_anexo = TRUE and (novo_anexo is null or novo_anexo = '') THEN
					SIGNAL SQLSTATE '45001'
                    SET MESSAGE_TEXT = 'Essa etapa exige envio de anexo';
				END IF;
            
            -- se for a última etapa, não cria nova etapa e atualiza o processo como concluído -- 
            IF id_ultima_etapa = id_etapa_final THEN
            
				update execucao_etapa set data_fim = now()
				where id_etapa = id_ultima_etapa
				and id_processo = novo_id_processo;
                
				update execucao_etapa set status_exec = 'CONCLUIDO'
				where id_etapa = id_ultima_etapa
				and id_processo = novo_id_processo;
                
                update processo set status_proc = 'CONCLUIDO'
                where id = novo_id_processo;
                
                LEAVE controle_insert;
			END IF;
		END IF;
    
	INSERT INTO execucao_etapa (id_processo, id_etapa, id_usuario, observacoes)
    VALUES (novo_id_processo, novo_id_etapa, novo_id_usuario, novo_observacoes);
    
    -- depois de inserir a etapa nova, atualiza a anterior como concluída e adiciona a data_fim -- 
	update execucao_etapa set data_fim = now()
    where id_etapa = id_ultima_etapa
    and id_processo = novo_id_processo;
    
    update execucao_etapa set status_exec = 'CONCLUIDO'
    where id_etapa = id_ultima_etapa
    and id_processo = novo_id_processo;
		END controle_insert;
END 
$$
DELIMITER ;

-- 4. TRIGGERS --
-- 4.1. VERIFICA SE O USUÁRIO INSERIDO EM EXECUCAO_ETAPA É RESPONSÁVEL PELA ETAPA EM QUESTÃO  -- 
DELIMITER $$
CREATE TRIGGER insertExecucao
	BEFORE INSERT ON execucao_etapa
    FOR EACH ROW
    BEGIN
		DECLARE cargo_res ENUM('ORIENTADOR', 'COORDENADOR', 'JIJ');
		DECLARE cargo_user ENUM('ORIENTADOR', 'COORDENADOR', 'JIJ');
        DECLARE msg_erro varchar(128);
    
		SELECT responsavel INTO cargo_res FROM etapa
		WHERE id = NEW.id_etapa;
    
		SELECT cargo INTO cargo_user FROM usuario
		WHERE id = NEW.id_usuario;
    
		IF cargo_user != cargo_res THEN
			SET msg_erro = CONCAT('Usuário inválido; responsável deve ser um', COALESCE(cargo_res, '[não informado]'));
			SIGNAL SQLSTATE'45000'
			SET MESSAGE_TEXT = msg_erro;
		END IF;
	END
$$ 
DELIMITER ;

-- 4.2. TRANSAÇÃO PARA, SE A EXECUÇÃO_ETAPA N. 1 FALHAR, NÃO HAVER INSERÇÃO DE NOVO PROCESSO -- 
DELIMITER $$
CREATE PROCEDURE criacaoProcessoEtapa(in novo_id_template bigint, in novo_id_usuario bigint, 
in novo_id_etapa bigint, in novo_observacoes text, in novo_anexo varchar(255))
BEGIN
	DECLARE novo_id_processo bigint;
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
        
START TRANSACTION;
	insert into processo (id_template, id_usuario) values
	(novo_id_template, novo_id_usuario); 
    
    SET novo_id_processo = LAST_INSERT_ID();
        
	CALL validacaoEtapas(novo_id_processo, novo_id_etapa, novo_id_usuario, novo_observacoes, novo_anexo);
    
    COMMIT;
    
END $$
DELIMITER ;

-- AUXILIARES -- 