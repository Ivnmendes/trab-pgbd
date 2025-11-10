use bdedica_wf;

insert into usuario (username, nome, cargo, senha) values 
('j.silva', 'João Silva', 'ORIENTADOR', '1234'),
('a.braga', 'Ana Braga', 'ORIENTADOR', '1234'),
('f.oliveira', 'Fernanda Oliveira', 'COORDENADOR', '4321'),
('b.rodrigues', 'Bruno Rodrigues', 'COORDENADOR', '4321'),
('m.souza', 'Mariana Souza', 'JIJ', '2143');
    
insert into template_processo(nome, descricao) values
('Envio de Relatórios', 'Cadastro e validação de relatórios para o JIJ'),
('Solicitação de Informações', 'Solicita informações referentes à MSE');

insert into etapa (id_template, nome, ordem, responsavel, campo_anexo) values
(1, 'Processo criado', 1, 'ORIENTADOR', false),
(1, 'Aguarda parecer do coordenador', 2, 'COORDENADOR', true),
(1, 'Aguarda correções no relatório', 3, 'ORIENTADOR', false),
(1, 'Enviado para conclusão', 4, 'JIJ', false),
(2, 'Processo criado', 1, 'JIJ', false),
(2, 'Aguarda retorno do coordenador', 2, 'COORDENADOR', false),
(2, 'Solicita dados ao orientador', 3, 'ORIENTADOR', false),
(2, 'Enviado para conclusão', 4, 'JIJ', false);

insert into fluxo_execucao (id_origem, id_destino) values
(1, 2), (2, 3), (2,4), (3,2), (4,4), (5,6), (6,8),(6,7), (7,6), (8,8), (8,6);

INSERT INTO processo (id_template, id_usuario, status_proc, data_inicio) VALUES
-- Template 1: Envio de Relatórios 
(1, 1, 'CONCLUIDO', '2025-09-10 08:15:00'),
(1, 1, 'PENDENTE',  '2025-09-25 10:00:00'),
(1, 2, 'PENDENTE',  '2025-10-03 09:30:00'),
(1, 2, 'CONCLUIDO', '2025-08-18 14:20:00'),
(1, 1, 'PENDENTE',  '2025-10-28 16:45:00'),
(1, 2, 'PENDENTE',  '2025-11-01 08:05:00'),
(1, 1, 'CONCLUIDO', '2025-07-30 13:40:00'),

-- Template 2: Solicitação de Informações 
(2, 5, 'PENDENTE',  '2025-09-05 09:10:00'),
(2, 5, 'CONCLUIDO', '2025-08-15 15:30:00'),
(2, 5, 'PENDENTE',  '2025-10-10 11:55:00'),
(2, 5, 'PENDENTE',  '2025-10-29 08:00:00'),
(2, 5, 'CONCLUIDO', '2025-09-22 17:00:00'),
(2, 5, 'PENDENTE',  '2025-11-01 09:10:00'),
(2, 5, 'PENDENTE',  '2025-11-07 10:45:00'),
(2, 5, 'CONCLUIDO', '2025-07-20 08:50:00');


INSERT INTO execucao_etapa (id_processo, id_etapa, id_usuario, observacoes, data_inicio, data_fim, status_exec)
VALUES
-- Processo 1: etapa 1 concluída, etapa 2 pendente
(1, 1, 1, 'Relatório inicial criado.', '2025-10-01 09:00:00', '2025-10-01 09:05:00', 'CONCLUIDO'),
(1, 2, 3, 'Aguardando análise do coordenador.', '2025-10-01 09:06:00', NULL, 'PENDENTE'),

-- Processo 2: etapa 1 concluída, etapa 2 concluída, etapa 3 pendente
(2, 1, 2, 'Correção feita e enviada.', '2025-09-28 10:00:00', '2025-09-28 10:05:00', 'CONCLUIDO'),
(2, 2, 4, 'Parecer dado, aguardando correção.', '2025-09-28 10:06:00', '2025-09-28 11:00:00', 'CONCLUIDO'),
(2, 3, 1, 'Devolvido para correções no relatório.', '2025-09-28 11:01:00', NULL, 'PENDENTE'),

-- Processo 3: concluído (etapa 4 finalizada)
(3, 1, 1, 'Processo iniciado.', '2025-09-15 08:00:00', '2025-09-15 08:03:00', 'CONCLUIDO'),
(3, 2, 3, 'Parecer favorável.', '2025-09-15 08:04:00', '2025-09-15 08:30:00', 'CONCLUIDO'),
(3, 4, 5, 'Conclusão pelo JIJ.', '2025-09-15 09:00:00', '2025-09-15 09:10:00', 'CONCLUIDO'),

-- Processo 4: etapa 2 pendente
(4, 1, 2, 'Relatório criado e enviado.', '2025-10-20 10:00:00', '2025-10-20 10:03:00', 'CONCLUIDO'),
(4, 2, 3, 'Aguardando análise.', '2025-10-20 10:05:00', NULL, 'PENDENTE'),

-- Processo 5: parado na etapa 3
(5, 1, 1, 'Primeiro envio.', '2025-09-30 14:00:00', '2025-09-30 14:02:00', 'CONCLUIDO'),
(5, 2, 3, 'Reprovado, precisa correção.', '2025-09-30 14:03:00', '2025-09-30 14:10:00', 'CONCLUIDO'),
(5, 3, 1, 'Revisando relatório.', '2025-09-30 14:11:00', NULL, 'PENDENTE'),

-- Processo 6: concluído
(6, 1, 2, 'Relatório inserido.', '2025-08-05 08:00:00', '2025-08-05 08:01:00', 'CONCLUIDO'),
(6, 2, 4, 'Análise feita.', '2025-08-05 08:05:00', '2025-08-05 08:20:00', 'CONCLUIDO'),
(6, 4, 5, 'Encerrado pelo JIJ.', '2025-08-05 08:21:00', '2025-08-05 08:25:00', 'CONCLUIDO'),

-- Processo 7: aguardando coordenador
(7, 1, 1, 'Correção feita.', '2025-10-25 09:00:00', '2025-10-25 09:03:00', 'CONCLUIDO'),
(7, 2, 4, 'Aguardando parecer.', '2025-10-25 09:04:00', NULL, 'PENDENTE'),

-- Processo 8: em etapa 3
(8, 1, 2, 'Processo iniciado.', '2025-09-02 08:00:00', '2025-09-02 08:03:00', 'CONCLUIDO'),
(8, 2, 4, 'Correção solicitada.', '2025-09-02 08:05:00', '2025-09-02 08:10:00', 'CONCLUIDO'),
(8, 3, 2, 'Em correção pelo orientador.', '2025-09-02 08:15:00', NULL, 'PENDENTE'),

-- Processo 9: aguardando conclusão
(9, 1, 1, 'Primeira etapa concluída.', '2025-09-10 07:00:00', '2025-09-10 07:02:00', 'CONCLUIDO'),
(9, 2, 3, 'Parecer positivo.', '2025-09-10 07:03:00', '2025-09-10 07:30:00', 'CONCLUIDO'),
(9, 4, 5, 'Aguardando finalização pelo JIJ.', '2025-09-10 07:40:00', NULL, 'PENDENTE'),

-- Processo 10: recém-criado, na etapa 2
(10, 1, 2, 'Envio inicial.', '2025-11-01 09:00:00', '2025-11-01 09:05:00', 'CONCLUIDO'),
(10, 2, 4, 'Em avaliação.', '2025-11-01 09:06:00', NULL, 'PENDENTE'),

-- PROCESSOS TEMPLATE 2 (Solicitação de Informações)
(11, 5, 5, 'Solicitação feita pelo JIJ.', '2025-10-15 10:00:00', '2025-10-15 10:03:00', 'CONCLUIDO'),
(11, 6, 3, 'Aguardando retorno do coordenador.', '2025-10-15 10:05:00', NULL, 'PENDENTE'),

(12, 5, 5, 'Nova solicitação.', '2025-09-25 08:00:00', '2025-09-25 08:02:00', 'CONCLUIDO'),
(12, 6, 4, 'Parecer emitido.', '2025-09-25 08:03:00', '2025-09-25 08:15:00', 'CONCLUIDO'),
(12, 8, 5, 'Encerrando processo.', '2025-09-25 08:20:00', NULL, 'PENDENTE'),

(13, 5, 5, 'Solicitação de dados iniciada.', '2025-09-18 11:00:00', '2025-09-18 11:03:00', 'CONCLUIDO'),
(13, 6, 4, 'Encaminhado ao coordenador.', '2025-09-18 11:04:00', NULL, 'PENDENTE'),

(14, 5, 5, 'Solicitação aberta.', '2025-09-30 09:00:00', '2025-09-30 09:03:00', 'CONCLUIDO'),
(14, 6, 3, 'Aguardando coordenador.', '2025-09-30 09:04:00', NULL, 'PENDENTE'),

(15, 5, 5, 'Solicitação de dados finalizada.', '2025-08-10 14:00:00', '2025-08-10 14:05:00', 'CONCLUIDO'),
(15, 6, 3, 'Retorno dado.', '2025-08-10 14:10:00', '2025-08-10 14:20:00', 'CONCLUIDO'),
(15, 8, 5, 'Finalizado.', '2025-08-10 14:25:00', '2025-08-10 14:30:00', 'CONCLUIDO');
