from django.contrib import admin
from torneio.models import Grupo, Selecao, Jogador, Jogo, EventoJogo

# Register your models here.

admin.register(Grupo)
admin.register(Selecao)
admin.register(Jogador)
admin.register(Jogo)
admin.register(EventoJogo)