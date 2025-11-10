-- CONSULTAS -- 

-- 1. TELA DE LISTA DE PROCESSOS -- 

-- 1.1. COORDENADOR E JIJ: MOSTRA TODOS OS PROCESSOS -- 
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
order by p.data_inicio DESC;

-- 1.1.1. FILTRO POR CONCLUÍDO/PENDENTE --
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
where p.status_proc = 'PENDENTE'; -- mudar conforme filtro

-- 1.1.2. FILTRO POR TIPO DE PROCESSO --
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
where tp.id = 1; -- mudar conforme filtro

-- 1.1.3. FILTRO POR USUÁRIO --
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
where u.id = 1;

-- 1.2. ORIENTADOR: MOSTRA SOMENTE OS PROCESSOS QUE ELE ESTÁ EM ALGUMA ETAPA -- 
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
where p.id in (select id_processo from execucao_etapa where
				id_usuario = 3); -- botar a variável do usuário aqui
                
-- 1.2.1. FILTRO POR CONCLUÍDO/PENDENTE --
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
where p.id in (select id_processo from execucao_etapa where
				id_usuario = 3) -- botar a variável do usuário aqui
and p.processo = 'PENDENTE'; -- variável

-- 1.2.2. FILTRO POR TIPO DE PROCESSO --
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id
where p.id in (select id_processo from execucao_etapa where
				id_usuario = 3) -- botar a variável do usuário aqui
and tp.id = 1; -- variável

-- 1.3. PARA TODOS USUÁRIOS: LISTA DE PROCESSOS QUE AGUARDAM ENCAMINHAMENTO DELES --
-- ESSA CONSULTA PODERIA APARECER NO TOPO DA TELA DE LISTA DE PROCESSOS, E ABAIXO "TODOS OS PROCESSOS"
select p.id as 'Id Processo', tp.nome as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em', e.nome as 'Etapa Pendente' from processo p join template_processo tp on p.id_template = tp.id
join usuario u on p.id_usuario = u.id join execucao_etapa ee on ee.id_processo = p.id join etapa e on e.id = ee.id_etapa
where p.id in (select id_processo from execucao_etapa where
				id_usuario = 1  -- botar a variável do usuário aqui
                and status_exec = 'PENDENTE'); 
                
-- mesma consulta, mas com visão --
select p.id as 'Id Processo', v1.nome_processo as 'Tipo Processo', u.nome as 'Processo iniciado por', p.status_proc as 'Status',
p.data_inicio as 'Iniciado em', v1.nome_etapa as 'Etapa Pendente' from processo p join v_etapa_processo v1 on p.id_template = v1.id_template
join usuario u on p.id_usuario = u.id join execucao_etapa ee on ee.id_processo = p.id and ee.id_etapa = v1.id_etapa
where ee.id_usuario = 1 and ee.status_exec = 'PENDENTE'; -- botar a variável do usuário aqui
                
-- 2. TELA DE ETAPAS DO PROCESSO (abre um processo e mostra todas as etapas do processo -- 
select e.nome as 'Etapa', u.nome as 'Encaminhado por', ee.status_exec as 'Status', ee.data_inicio as 'Data Início',
ee.data_fim as 'Data Fim', ee.observacoes as 'Mensagem' from etapa e join execucao_etapa ee on e.id = ee.id_etapa
join usuario u on u.id = ee.id_usuario 
where id_processo = 5
order by status_exec, data_fim desc; 
