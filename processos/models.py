from django.db import models
from usuarios.models import Usuario

class TemplateProcesso(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'templateProcesso'


class Etapa(models.Model):
    id = models.AutoField(primary_key=True)
    id_template = models.ForeignKey(
        TemplateProcesso, 
        on_delete=models.DO_NOTHING, 
        db_column='id_template',
        db_constraint=False 
    )
    nome = models.CharField(max_length=255)
    ordem = models.IntegerField()
    responsavel = models.CharField(max_length=100) 

    class Meta:
        managed = False
        db_table = 'etapa'


class FluxoExecucao(models.Model):
    id = models.AutoField(primary_key=True)
    id_origem = models.ForeignKey(
        Etapa, 
        on_delete=models.DO_NOTHING, 
        related_name='fluxo_origem',
        db_column='id_origem',
        db_constraint=False
    )
    id_destino = models.ForeignKey(
        Etapa, 
        on_delete=models.DO_NOTHING, 
        related_name='fluxo_destino',
        db_column='id_destino',
        db_constraint=False
    )

    class Meta:
        managed = False
        db_table = 'fluxo_execucao'


class Processo(models.Model):
    id = models.AutoField(primary_key=True)
    id_template = models.ForeignKey(
        TemplateProcesso, 
        on_delete=models.DO_NOTHING,
        db_column='id_template',
        db_constraint=False
    )
    id_usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.DO_NOTHING,
        db_column='id_usuario',
        db_constraint=False
    )
    status = models.CharField(max_length=100)
    data_inicio = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'processo'


class ExecucaoEtapa(models.Model):
    id = models.AutoField(primary_key=True)
    id_processo = models.ForeignKey(
        Processo, 
        on_delete=models.DO_NOTHING,
        db_column='id_processo',
        db_constraint=False
    )
    id_etapa = models.ForeignKey(
        Etapa, 
        on_delete=models.DO_NOTHING,
        db_column='id_etapa',
        db_constraint=False
    )
    id_usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.DO_NOTHING,
        db_column='id_usuario',
        db_constraint=False,
        blank=True, 
        null=True 
    )
    observacoes = models.TextField(blank=True, null=True)
    data_inicio = models.DateTimeField(blank=True, null=True)
    data_fim = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'execucao_etapa'


class ModeloCampo(models.Model):
    id = models.AutoField(primary_key=True)
    id_etapa = models.ForeignKey(
        Etapa, 
        on_delete=models.DO_NOTHING,
        db_column='id_etapa',
        db_constraint=False
    )
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=100)
    obrigatorio = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'modelo_campo'


class Campo(models.Model):
    id = models.AutoField(primary_key=True)
    id_modelo = models.ForeignKey(
        ModeloCampo, 
        on_delete=models.DO_NOTHING,
        db_column='id_modelo',
        db_constraint=False
    )
    id_exec_etapa = models.ForeignKey(
        ExecucaoEtapa, 
        on_delete=models.DO_NOTHING,
        db_column='id_exec_etapa',
        db_constraint=False
    )
    dados = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'campo'