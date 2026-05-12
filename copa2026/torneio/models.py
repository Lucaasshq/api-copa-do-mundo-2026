from django.db.models import Model, CharField, TextField, ForeignKey, OneToOneField, URLField, DateField, PositiveSmallIntegerField, BooleanField, DateTimeField, CASCADE, PROTECT, SET_NULL
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Grupo(Model):
    nome = CharField(max_length=1, null=False, blank=False,)
    descricao = TextField(blank=True)
    
    def __str__(self):
        return f"Grupo {self.nome} - {self.descricao}"


class Tecnico(Model):
    nome = CharField(max_length=150)
    nacionalidade = CharField(max_length=100)
    data_nascimento = DateField()
    
    def __str__(self):
        return f"{self.nome} - {self.nacionalidade}"

class Selecao(Model):
    confederacoes = [
        ("UEFA", "UEFA"),
        ("CONMEBOL", "CONMEBOL"),
        ("CONCACAF", "CONCACAF"),
        ("CAF", "CAF"),
        ("AFC", "AFC"),
        ("OFC", "OFC")
    ]
    
    nome = CharField(max_length=100, null=False, blank=False)
    sigla = CharField(max_length=3, unique=True, null=False, blank=False)
    confederacao = CharField(choices=confederacoes, max_length=20, null=False, blank=False)
    grupo = ForeignKey(Grupo, on_delete=PROTECT, related_name='selecoes')
    tecnico = OneToOneField(Tecnico, on_delete=SET_NULL, null=True, related_name='selecao')
    escudo_url = URLField(blank=True)
    
    def __str__(self):
        return f"{self.nome} - {self.sigla} - {self.confederacao} - {self.grupo}"
    
class Jogador(Model):
    posicoes = [
        ("GOLEIRO", "Goleiro"),
        ("ZAGUEIRO", "Zagueiro"),
        ("LATERAL", "Lateral"),
        ("VOLANTE", "Volante"),
        ("MEIA", "Meia"),
        ("ATACANTE", "Atacante"),
    ]
    
    numeros_validos = [
        MinValueValidator(1),
        MaxValueValidator(26)
    ]
    
    nome = CharField(max_length=150)
    nome_guerra = CharField(max_length=50)
    selecao = ForeignKey(Selecao, on_delete=PROTECT, related_name='jogadores')
    posicao = CharField(choices=posicoes, max_length=20, null=False, blank=False)
    numero_camisa = PositiveSmallIntegerField(validators=numeros_validos, null=False, blank=False, help_text="Insira um valor entre 1 e 26")
    data_nascimento = DateField()
    suspenso = BooleanField(default=False, null=False, blank=False)
    
    def __str__(self):
        return f"{self.nome_guerra} - {self.posicao} - {self.numero_camisa} - {self.selecao}"
    
    
class Jogo(Model):
    fases = [
        ('GRUPOS', 'Grupos'),
        ('FASE32', '32 avos'),
        ('OITAVAS', 'grupos'),
        ('QUARTAS', 'Quartas'),
        ('SEMIFINAL', 'Semifinal'),
        ('FINAL', 'final'),
    ]
    
    status_jogo = [
        ('AGENDADO', 'Agendado'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('ENCERRADO', 'Encerrado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    selecao_mandante = ForeignKey(Selecao, on_delete=PROTECT, related_name='jogos_mandante')
    selecao_visitante = ForeignKey(Selecao, on_delete=PROTECT, related_name='jogos_visitante')
    fase = CharField(choices=fases, max_length=20, null=False, blank=False)
    grupo = ForeignKey(Grupo, on_delete=PROTECT, null=True, blank=True)
    data_hora = DateTimeField()
    estadio = CharField(max_length=150, blank=True)
    cidade = CharField(max_length=150, blank=True)
    gols_mandante = PositiveSmallIntegerField(default=0)
    gols_visitante = PositiveSmallIntegerField(default=0)
    status = CharField(choices=status_jogo, max_length=20, null=False, blank=False)
    
    def gol_mandante(self):
        self.gols_mandante += 1
    
    def gol_visitante(self):
        self.gols_visitante += 1
     
    def __str__(self):
        return f"{self.selecao_mandante} - {self.selecao_visitante} - {self.fase} - {self.grupo} - Placar: {self.gols_mandante} X {self.gols_visitante}"
    
class EventoJogo(Model):
    eventos = [
        ('GOL', 'Gol'),
        ('CARTAO_AMARELO', 'Cartão amarelo'),
        ('CARTAO_VERMELHO', 'Cartão vermelho'),
        ('GOL_CONTRA', 'Gol contra'),
    ]
    
    minutos_validos = [
        MinValueValidator(1),
        MaxValueValidator(120)
    ]
    
    jogo = ForeignKey(Jogo, on_delete=CASCADE, related_name='eventos')
    jogador = ForeignKey(Jogador, on_delete=PROTECT, related_name='eventos')
    tipo = CharField(choices=eventos, max_length=20, null=False, blank=False)
    minuto = PositiveSmallIntegerField(validators=minutos_validos, null=False, blank=False)
    acrescimo = BooleanField(default=False, null=False, blank=False)
    
    def __str__(self):
        return f"{self.tipo} - {self.minuto}' - {self.jogador.nome_guerra} - {self.jogo}"
    
    def save(self, *args, **kwargs):
        evento_novo = self.pk is None
        
        super().save(*args, **kwargs)

        if evento_novo:
            self.processar_regras_negocio()

    def processar_regras_negocio(self):
        jogo = self.jogo
        jogador = self.jogador

        if self.tipo == 'CARTAO_VERMELHO':
            jogador.suspenso = True
            jogador.save()
            
        elif self.tipo == 'CARTAO_AMARELO':
            amarelos_no_jogo = EventoJogo.objects.filter(
                jogo=jogo, 
                jogador=jogador, 
                tipo='CARTAO_AMARELO'
            ).exclude(pk=self.pk).count()
            
            if amarelos_no_jogo >= 1:
                jogador.suspenso = True
                jogador.save()

        jogador_e_mandante = (jogador.selecao == jogo.selecao_mandante)

        if self.tipo == 'GOL':
            if jogador_e_mandante:
                jogo.gol_mandante()
            else:
                jogo.gol_visitante()
            jogo.save()

        elif self.tipo == 'GOL_CONTRA':
            if jogador_e_mandante:
                jogo.gols_visitante += 1
            else:
                jogo.gols_mandante += 1
            jogo.save()