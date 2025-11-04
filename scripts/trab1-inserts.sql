use bdedica;
insert into usuario (username, nome, cargo, senha) values 
	('j.silva', 'João Silva', 'ORIENTADOR', '1234'),
    ('a.braga', 'Ana Braga', 'ORIENTADOR', '1234'),
    ('f.oliveira', 'Fernanda Oliveira', 'COORDENADOR', '4321'),
    ('m.souza', 'Mariana Souza', 'JIJ', '2143');
    
    
insert into adolescente (nome) values
	('Dionatan Melo'),
    ('Michele Souza'),
    ('Stefany Vargas'),
    ('Enzo Fabio');
    
insert into mse (id_adolescente, id_orientador, semanas_totais, semanas_restantes, status_mse) values
(1, 1, 27, 27, 'EM_ANDAMENTO'),
(2, 2, 24, 24, 'EM_ANDAMENTO'),
(3, 1, 27, 27, 'EM_ANDAMENTO'),
(4, 2, 54, 54, 'EM_ANDAMENTO');

insert into relatorio (id_mse, mes, ano, presencas, faltas, relato, status_rel) values
(2, 'maio', 2024, 1, 3, 'blablablablabla', 'PENDENTE');
insert into relatorio (id_mse, mes, ano, presencas, faltas, relato, status_rel) values
(1, 'dezembro', 2025, 4, 0, 'blablablablabla', 'PENDENTE');