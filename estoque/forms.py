from django import forms
from django.contrib.auth.models import User, Group
from .models import Produto

class UsuarioForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput)
    grupo = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label="Selecione o setor")

    class Meta:
        model = User
        fields = ['username', 'email', 'senha', 'grupo']

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'quantidade', 'observacoes', 'setor_responsavel']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Se não for ADMIN, só deixa o próprio setor e bloqueia o campo
            if not user.groups.filter(name='ADMIN').exists() and not user.is_superuser:
                self.fields['setor_responsavel'].queryset = user.groups.all()
                self.fields['setor_responsavel'].initial = user.groups.first()
                self.fields['setor_responsavel'].disabled = True
        