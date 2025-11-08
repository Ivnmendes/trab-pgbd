from rest_framework import serializers

class TemplateProcessoSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de um TemplateProcesso.
    """
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(max_length=255)
    descricao = serializers.CharField(allow_blank=True, required=False)


class ProcessoSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de um Processo.
    """
    id = serializers.IntegerField(read_only=True)
    id_template = serializers.IntegerField()
    id_usuario = serializers.IntegerField()
    status_proc = serializers.CharField(max_length=50)
    data_inicio = serializers.DateTimeField()


class EtapaSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de uma Etapa.
    """
    id = serializers.IntegerField(read_only=True)
    id_template = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)
    ordem = serializers.IntegerField()
    responsavel = serializers.CharField(max_length=100)


class FluxoExecucaoSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de um FluxoExecucao.
    """
    id = serializers.IntegerField(read_only=True)
    id_origem = serializers.IntegerField()
    id_destino = serializers.IntegerField()


class ModeloCampoSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de um ModeloCampo.
    """
    id = serializers.IntegerField(read_only=True)
    id_etapa = serializers.IntegerField()
    nome_campo = serializers.CharField(max_length=255)
    tipo = serializers.CharField(max_length=100)
    obrigatorio = serializers.BooleanField()


class CampoSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de um CampoPreenchido.
    """
    id = serializers.IntegerField(read_only=True)
    id_modelo = serializers.IntegerField()
    id_exec_etapa = serializers.IntegerField()
    dados = serializers.CharField(allow_blank=True, required=False)


class ExecucaoEtapaSerializer(serializers.Serializer):
    """
    Valida os dados para criação e atualização de uma ExecucaoEtapa.
    """
    id = serializers.IntegerField(read_only=True)
    id_processo = serializers.IntegerField()
    id_etapa = serializers.IntegerField()
    id_usuario = serializers.IntegerField(allow_null=True, required=False)
    observacoes = serializers.CharField(allow_blank=True, required=False)
    data_inicio = serializers.DateTimeField(allow_null=True, required=False)
    data_fim = serializers.DateTimeField(allow_null=True, required=False)
    status = serializers.CharField(max_length=100)