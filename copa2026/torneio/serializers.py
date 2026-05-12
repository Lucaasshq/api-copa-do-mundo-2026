from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField
from .models import Grupo, Tecnico, Selecao, Jogador, Jogo, EventoJogo


class GrupoSerializer(ModelSerializer):
    class Meta:
        model = Grupo
        fields = '__all__'


class TecnicoSerializer(ModelSerializer):
    class Meta:
        model = Tecnico
        fields = '__all__'


class SelecaoSerializer(ModelSerializer):
    tecnico_nome = CharField(
        source='tecnico.nome',
        read_only=True
    )

    class Meta:
        model = Selecao
        fields = '__all__'


class JogadorSerializer(ModelSerializer):
    posicao_display = CharField(
        source='get_posicao_display',
        read_only=True
    )

    class Meta:
        model = Jogador
        fields = '__all__'


class EventoJogoSerializer(ModelSerializer):
    jogador_nome = CharField(
        source='jogador.nome_guerra',
        read_only=True
    )

    tipo_display = CharField(
        source='get_tipo_display',
        read_only=True
    )

    class Meta:
        model = EventoJogo
        fields = '__all__'


class JogoSerializer(ModelSerializer):
    mandante_nome = CharField(
        source='selecao_mandante.nome',
        read_only=True
    )

    visitante_nome = CharField(
        source='selecao_visitante.nome',
        read_only=True
    )

    fase_display = CharField(
        source='get_fase_display',
        read_only=True
    )

    eventos = EventoJogoSerializer(
        many=True,
        required=False
    )

    resultado = SerializerMethodField()

    class Meta:
        model = Jogo
        fields = '__all__'

    def get_resultado(self, obj):
        if obj.gols_mandante > obj.gols_visitante:
            return 'Mandante venceu'

        elif obj.gols_visitante > obj.gols_mandante:
            return 'Visitante venceu'

        return 'Empate'

    def create(self, validated_data):
        eventos_data = validated_data.pop('eventos', [])

        jogo = Jogo.objects.create(**validated_data)

        for evento_data in eventos_data:
            EventoJogo.objects.create(
                jogo=jogo,
                **evento_data
            )
        return jogo