from django.db import models
from django.contrib.auth.models import Group, User  # já importa User e Group

class Produto(models.Model):
    nome = models.CharField(max_length=100)  # Nome do produto
    quantidade = models.IntegerField(default=0)  # Quantidade em estoque
    setor_responsavel = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    data_entrada = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('nome', 'setor_responsavel')
        verbose_name_plural = "Produtos"

    def __str__(self):
        return f"{self.nome} ({self.quantidade})"


class Movimentacao(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    )

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tipo} - {self.produto.nome} ({self.quantidade})"


class Notificacao(models.Model):
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    setor = models.ForeignKey('auth.Group', null=True, blank=True, on_delete=models.SET_NULL)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titulo

class LeituraNotificacao(models.Model):
    notificacao = models.ForeignKey(Notificacao, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    lida = models.BooleanField(default=False)

    class Meta:
        unique_together = ('notificacao', 'usuario')


class Setor(models.Model):
    nome_setor = models.CharField(max_length=100, default='Sem Nome')

    def __str__(self):
        return self.nome_setor


class Colaborador(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Protocolo(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    patrimonio = models.CharField(max_length=50)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.colaborador} - {self.item} ({self.patrimonio})"