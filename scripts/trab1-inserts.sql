use bdedica_wf;
insert into usuario (username, nome, cargo, senha) values 
	('j.silva', 'João Silva', 'ORIENTADOR', '1234'),
    ('a.braga', 'Ana Braga', 'ORIENTADOR', '1234'),
    ('f.oliveira', 'Fernanda Oliveira', 'COORDENADOR', '4321'),
    ('b.rodrigues', 'Bruno Rodrigues', 'COORDENADOR', '4321'),
    ('m.souza', 'Mariana Souza', 'JIJ', '2143');
    
insert into template_processo(nome, descricao) values
	('Envio de Relatórios', 'Cadastro e validação de relatórios para o JIJ');
    
insert into etapa (id_template, nome, ordem, responsavel) values
(1, 'Enviado para correção', 1, 'ORIENTADOR'),
(1, 'Aguarda parecer do coordenador', 2, 'COORDENADOR'),
(1, 'Aguarda correções no relatório', 3, 'ORIENTADOR'),
(1, 'Enviado para conclusão', 4, 'JIJ');

insert into fluxo_execucao (id_origem, id_destino) values
(1, 2), (2, 3), (2,4), (3,2), (4,4);

insert into modelo_campo(id_etapa, nome_campo, tipo, obrigatorio) values
(1, 'Relatório', 'ARQUIVO', true),
(3, 'Relatório', 'ARQUIVO', true);
