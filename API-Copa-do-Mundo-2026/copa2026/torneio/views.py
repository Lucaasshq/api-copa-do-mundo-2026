from collections import defaultdict

from django.db.models import Q, Count
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Grupo,
    Tecnico,
    Selecao,
    Jogador,
    Jogo,
    EventoJogo
)

from .serializers import (
    GrupoSerializer,
    TecnicoSerializer,
    SelecaoSerializer,
    JogadorSerializer,
    JogoSerializer,
    EventoJogoSerializer
)


class GrupoViewSet(ModelViewSet):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer

    @action(detail=True, methods=['get'])
    def classificacao(self, request, pk=None):
        grupo = self.get_object()

        selecoes = grupo.selecoes.all()

        jogos = Jogo.objects.filter(
            grupo=grupo,
            status='ENCERRADO'
        ).select_related(
            'selecao_mandante',
            'selecao_visitante'
        )

        tabela = defaultdict(lambda: {
            'selecao': '',
            'sigla': '',
            'grupo': grupo.nome,
            'jogos': 0,
            'vitorias': 0,
            'empates': 0,
            'derrotas': 0,
            'gols_pro': 0,
            'gols_contra': 0,
            'saldo': 0,
            'pontos': 0,
        })

        for selecao in selecoes:
            tabela[selecao.id]['selecao'] = selecao.nome
            tabela[selecao.id]['sigla'] = selecao.sigla

        for jogo in jogos:
            mandante = jogo.selecao_mandante
            visitante = jogo.selecao_visitante

            gols_m = jogo.gols_mandante
            gols_v = jogo.gols_visitante

            tabela[mandante.id]['jogos'] += 1
            tabela[visitante.id]['jogos'] += 1

            tabela[mandante.id]['gols_pro'] += gols_m
            tabela[mandante.id]['gols_contra'] += gols_v

            tabela[visitante.id]['gols_pro'] += gols_v
            tabela[visitante.id]['gols_contra'] += gols_m

            if gols_m > gols_v:
                tabela[mandante.id]['vitorias'] += 1
                tabela[mandante.id]['pontos'] += 3

                tabela[visitante.id]['derrotas'] += 1

            elif gols_v > gols_m:
                tabela[visitante.id]['vitorias'] += 1
                tabela[visitante.id]['pontos'] += 3

                tabela[mandante.id]['derrotas'] += 1

            else:
                tabela[mandante.id]['empates'] += 1
                tabela[visitante.id]['empates'] += 1

                tabela[mandante.id]['pontos'] += 1
                tabela[visitante.id]['pontos'] += 1

        classificacao = []

        for selecao_id, dados in tabela.items():
            dados['saldo'] = (
                dados['gols_pro'] - dados['gols_contra']
            )

            dados['selecao_id'] = selecao_id

            classificacao.append(dados)

        classificacao.sort(
            key=lambda x: (
                x['pontos'],
                x['saldo'],
                x['gols_pro']
            ),
            reverse=True
        )

        for index, item in enumerate(classificacao, start=1):
            item['posicao'] = index

        return Response(classificacao)


class TecnicoViewSet(ModelViewSet):
    queryset = Tecnico.objects.all()
    serializer_class = TecnicoSerializer

    filter_backends = [SearchFilter]
    search_fields = ['nome']


class SelecaoViewSet(ModelViewSet):
    queryset = Selecao.objects.all()
    serializer_class = SelecaoSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter
    ]

    filterset_fields = ['grupo']

    search_fields = [
        'nome',
        'sigla'
    ]


class JogadorViewSet(ModelViewSet):
    queryset = Jogador.objects.select_related(
        'selecao'
    ).all()

    serializer_class = JogadorSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_fields = [
        'selecao',
        'posicao',
        'suspenso'
    ]

    search_fields = [
        'nome',
        'nome_guerra'
    ]

    ordering_fields = [
        'selecao',
        'numero_camisa'
    ]

    @action(detail=False, methods=['get'])
    def suspensos(self, request):
        jogadores = Jogador.objects.filter(
            suspenso=True
        ).select_related('selecao')

        resultado = []

        for jogador in jogadores:
            possui_vermelho = EventoJogo.objects.filter(
                jogador=jogador,
                tipo='CARTAO_VERMELHO'
            ).exists()

            if possui_vermelho:
                motivo = 'Cartão vermelho'

            else:
                amarelos = EventoJogo.objects.filter(
                    jogador=jogador,
                    tipo='CARTAO_AMARELO'
                ).count()

                if amarelos >= 2:
                    motivo = 'Acúmulo de amarelos'
                else:
                    motivo = 'Suspensão indefinida'

            resultado.append({
                'jogador': jogador.nome_guerra,
                'nome_completo': jogador.nome,
                'selecao': jogador.selecao.nome,
                'sigla': jogador.selecao.sigla,
                'motivo': motivo
            })

        return Response(resultado)


class JogoViewSet(ModelViewSet):
    queryset = Jogo.objects.select_related(
        'selecao_mandante',
        'selecao_visitante',
        'grupo'
    ).prefetch_related(
        'eventos',
        'eventos__jogador'
    ).all()

    serializer_class = JogoSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_fields = [
        'fase',
        'status',
        'grupo'
    ]

    search_fields = [
        'estadio',
        'cidade'
    ]

    ordering_fields = [
        'data_hora'
    ]

    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        jogo = self.get_object()

        eventos = jogo.eventos.select_related(
            'jogador',
            'jogador__selecao'
        )

        gols_mandante = []
        gols_visitante = []

        amarelos_mandante = []
        amarelos_visitante = []

        vermelhos_mandante = []
        vermelhos_visitante = []

        for evento in eventos:
            jogador = evento.jogador

            evento_info = {
                'jogador': jogador.nome_guerra,
                'minuto': evento.minuto
            }

            jogador_mandante = (
                jogador.selecao_id == jogo.selecao_mandante_id
            )

            if evento.tipo in ['GOL', 'GOL_CONTRA']:
                if evento.tipo == 'GOL':
                    if jogador_mandante:
                        gols_mandante.append(evento_info)
                    else:
                        gols_visitante.append(evento_info)

                elif evento.tipo == 'GOL_CONTRA':
                    if jogador_mandante:
                        gols_visitante.append(evento_info)
                    else:
                        gols_mandante.append(evento_info)

            elif evento.tipo == 'CARTAO_AMARELO':
                if jogador_mandante:
                    amarelos_mandante.append(evento_info)
                else:
                    amarelos_visitante.append(evento_info)

            elif evento.tipo == 'CARTAO_VERMELHO':
                if jogador_mandante:
                    vermelhos_mandante.append(evento_info)
                else:
                    vermelhos_visitante.append(evento_info)

        if jogo.gols_mandante > jogo.gols_visitante:
            resultado = 'Mandante venceu'

        elif jogo.gols_visitante > jogo.gols_mandante:
            resultado = 'Visitante venceu'

        else:
            resultado = 'Empate'

        return Response({
            'jogo': {
                'mandante': jogo.selecao_mandante.nome,
                'visitante': jogo.selecao_visitante.nome,
            },

            'placar': {
                'mandante': {
                    'gols': jogo.gols_mandante,
                    'autores': gols_mandante
                },
                'visitante': {
                    'gols': jogo.gols_visitante,
                    'autores': gols_visitante
                }
            },

            'cartoes': {
                'mandante': {
                    'amarelos': amarelos_mandante,
                    'vermelhos': vermelhos_mandante
                },
                'visitante': {
                    'amarelos': amarelos_visitante,
                    'vermelhos': vermelhos_visitante
                }
            },

            'resultado': resultado,
            'status': jogo.status
        })

    @action(detail=False, methods=['post'], url_path='avancar-fase')
    def avancar_fase(self, request):
        jogos_grupos = Jogo.objects.filter(
            fase='GRUPOS'
        )

        jogos_nao_encerrados = jogos_grupos.exclude(
            status='ENCERRADO'
        )

        if jogos_nao_encerrados.exists():
            return Response(
                {
                    'erro': 'Ainda existem jogos da fase de grupos não encerrados.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        grupos = Grupo.objects.all()

        classificados = []

        for grupo in grupos:
            selecoes = grupo.selecoes.all()

            tabela = defaultdict(lambda: {
                'selecao': '',
                'sigla': '',
                'grupo': grupo.nome,
                'jogos': 0,
                'vitorias': 0,
                'empates': 0,
                'derrotas': 0,
                'gols_pro': 0,
                'gols_contra': 0,
                'saldo': 0,
                'pontos': 0,
            })

            for selecao in selecoes:
                tabela[selecao.id]['selecao'] = selecao.nome
                tabela[selecao.id]['sigla'] = selecao.sigla

            jogos = jogos_grupos.filter(
                grupo=grupo
            )

            for jogo in jogos:
                mandante = jogo.selecao_mandante
                visitante = jogo.selecao_visitante

                gm = jogo.gols_mandante
                gv = jogo.gols_visitante

                tabela[mandante.id]['jogos'] += 1
                tabela[visitante.id]['jogos'] += 1

                tabela[mandante.id]['gols_pro'] += gm
                tabela[mandante.id]['gols_contra'] += gv

                tabela[visitante.id]['gols_pro'] += gv
                tabela[visitante.id]['gols_contra'] += gm

                if gm > gv:
                    tabela[mandante.id]['vitorias'] += 1
                    tabela[mandante.id]['pontos'] += 3

                    tabela[visitante.id]['derrotas'] += 1

                elif gv > gm:
                    tabela[visitante.id]['vitorias'] += 1
                    tabela[visitante.id]['pontos'] += 3

                    tabela[mandante.id]['derrotas'] += 1

                else:
                    tabela[mandante.id]['empates'] += 1
                    tabela[visitante.id]['empates'] += 1

                    tabela[mandante.id]['pontos'] += 1
                    tabela[visitante.id]['pontos'] += 1

            ranking = []

            for selecao_id, dados in tabela.items():
                dados['saldo'] = (
                    dados['gols_pro'] - dados['gols_contra']
                )

                ranking.append(dados)

            ranking.sort(
                key=lambda x: (
                    x['pontos'],
                    x['saldo'],
                    x['gols_pro']
                ),
                reverse=True
            )

            for posicao, item in enumerate(ranking, start=1):
                item['posicao_grupo'] = posicao

            classificados.extend(ranking[:2])

        classificados.sort(
            key=lambda x: (
                x['pontos'],
                x['saldo'],
                x['gols_pro']
            ),
            reverse=True
        )

        return Response({
            'fase_origem': 'grupos',
            'fase_destino': 'fase32',
            'classificados': classificados,
            'total_classificados': len(classificados)
        })


class EventoJogoViewSet(ModelViewSet):
    queryset = EventoJogo.objects.all()
    serializer_class = EventoJogoSerializer

    filter_backends = [
        DjangoFilterBackend
    ]

    filterset_fields = [
        'jogo',
        'jogador',
        'tipo'
    ]