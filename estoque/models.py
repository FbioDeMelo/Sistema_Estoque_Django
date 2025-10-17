from django.db import models
from django.contrib.auth.models import Group, User
from django.utils import timezone

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
    item = models.ForeignKey(Produto, on_delete=models.CASCADE)
    item_nome = models.CharField(max_length=100, blank=True, null=True)
    patrimonio = models.CharField(max_length=50, unique=True)  # obrigatório
    data = models.DateTimeField(auto_now_add=True)


# =========================
# Notificações
# =========================
from django.db import models
from django.contrib.auth.models import Group
from .models import Produto  # ajuste se necessário

class Notificacao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True)  # deixa opcional
    setor = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    mensagem = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)
    vista = models.BooleanField(default=False)  # caso já tenha mudado 'lida' para 'vista'

    def __str__(self):
        return f"{self.produto} - {self.mensagem}"

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.produto.nome} - {'Vista' if self.vista else 'Nova'}"
# models.py
from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar_url = models.URLField(
        max_length=500,
        default='https://cdn-icons-png.flaticon.com/512/149/149071.png'
    )

    def __str__(self):
        return self.user.username
