from django.shortcuts import render, redirect, get_object_or_404
from .models import Produto
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from .forms import UsuarioForm, ProdutoForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Movimentacao
import csv
import json
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
# -------------------- View do Estoque --------------------
@login_required(login_url='login')
def index(request):
    user_groups = request.user.groups.all()
    is_admin = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser

    if is_admin:
        setores = Group.objects.all()
    else:
        setores = user_groups

    hub_info = []
    for setor in setores:
        produtos_setor = Produto.objects.filter(setor_responsavel=setor)
        hub_info.append({
            'nome_setor': setor.name,
            'total_produtos': produtos_setor.count()
        })

    total_produtos = sum([s['total_produtos'] for s in hub_info])

    if is_admin:
        chart_labels = [s['nome_setor'] for s in hub_info]
        chart_data = [s['total_produtos'] for s in hub_info]
    else:
        chart_labels = []
        chart_data = []

    return render(request, 'estoque/index.html', {
        'hub_info': hub_info,
        'is_admin': is_admin,
        'total_produtos': total_produtos,
        # >>> AQUI <<<
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })
# -------------------- Função para verificar se é ADMIN --------------------
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists() or user.is_superuser

# -------------------- View para Adicionar Usuário --------------------
@login_required(login_url='login')
@user_passes_test(is_admin)
def adicionar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['senha']
            )
            grupo = form.cleaned_data['grupo']
            usuario.groups.add(grupo)
            return redirect('index')
    else:
        form = UsuarioForm()

    # Contexto extra para sidebar
    user_groups = request.user.groups.all()
    is_admin_flag = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser
    if is_admin_flag:
        setores = Group.objects.all()
    else:
        setores = user_groups
    hub_info = [{'nome_setor': s.name, 'total_produtos': Produto.objects.filter(setor_responsavel=s).count()} for s in setores]

    return render(request, 'estoque/adicionar_usuario.html', {
        'form': form,
        'is_admin': is_admin_flag,
        'hub_info': hub_info
    })

@login_required(login_url='login')
def adicionar_produto(request):
    is_admin = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser

    if request.method == 'POST':
        nome = request.POST.get('nome')
        quantidade = request.POST.get('quantidade') 
      
        if is_admin:
            setor_id = request.POST.get('setor_responsavel')
            setor = Group.objects.get(id=setor_id)  # <-- transforma o id em objeto
        else:
            setor = request.user.groups.first()

        existente = Produto.objects.filter(
            nome__icontains=nome,
            setor_responsavel=setor
        ).first()   

        if existente:       
            existente.quantidade += int(quantidade)
            existente.observacoes = request.POST.get('observacoes', existente.observacoes)
            existente.save()
            produto = existente
        else:
            produto = Produto.objects.create(
                nome=nome,
                quantidade=quantidade,
                setor_responsavel=setor,
                observacoes=request.POST.get('observacoes', '')
            )

        # registra movimentação de ENTRADA
        Movimentacao.objects.create(
            produto=produto,
            usuario=request.user,
            tipo='entrada',
            quantidade=quantidade,
            observacao='Cadastro ou incremento via form'
        )

        return redirect('index')

    form = ProdutoForm(user=request.user)     
    return render(request, 'estoque/adicionar_produto.html', {
        'form': form,
        'is_admin': is_admin,
    })

@login_required(login_url='login')
def produtos_setor(request, setor):
    user_groups = request.user.groups.all()
    is_admin = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser

    if not is_admin and setor not in [g.name for g in user_groups]:
        return redirect('index')

    if is_admin and setor == 'todos':
        produtos = Produto.objects.all()
    else:
        produtos = Produto.objects.filter(setor_responsavel__name=setor)

    # Prepara hub_info para a sidebar
    if is_admin:
        setores = Group.objects.all()
    else:
        setores = user_groups

    hub_info = []
    for s in setores:
        produtos_setor = Produto.objects.filter(setor_responsavel=s)
        hub_info.append({
            'nome_setor': s.name,
            'total_produtos': produtos_setor.count()
        })

    context = {
        'produtos': produtos,
        'setor': setor,
        'is_admin': is_admin,
        'hub_info': hub_info,
    }
    return render(request, 'estoque/produtos.html', context)


# -------------------- View para Gerenciar Usuários --------------------
@login_required(login_url='login')
@user_passes_test(is_admin)
def gerenciar_usuarios(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        usuario = get_object_or_404(User, id=user_id)
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario.username = form.cleaned_data['username']
            usuario.email = form.cleaned_data['email']
            if form.cleaned_data['senha']:
                usuario.set_password(form.cleaned_data['senha'])
            usuario.save()
            grupo = form.cleaned_data['grupo']
            usuario.groups.clear()
            usuario.groups.add(grupo)
            return redirect('gerenciar_usuarios')

    usuarios = User.objects.all()
    grupos = Group.objects.all()

    # Adicionando hub_info e is_admin para a sidebar
    user_groups = request.user.groups.all()
    is_admin_flag = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser

    if is_admin_flag:
        setores = Group.objects.all()
    else:
        setores = user_groups

    hub_info = []
    for s in setores:
        produtos_setor = Produto.objects.filter(setor_responsavel=s)
        hub_info.append({
            'nome_setor': s.name,
            'total_produtos': produtos_setor.count()
        })

    context = {
        'usuarios': usuarios,
        'groups': grupos,
        'is_admin': is_admin_flag,
        'hub_info': hub_info,
    }

    return render(request, 'estoque/gerenciar_usuarios.html', context)

@login_required(login_url='login')
@require_POST
def retirar_item(request, produto_id):
    try:
        quantidade = int(request.POST.get('quantidade', 0))
        produto = Produto.objects.get(id=produto_id)

        # verifica se o usuário pode mexer nesse produto
        is_admin = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser
        if not is_admin and produto.setor_responsavel not in request.user.groups.all():
            return JsonResponse({'error': 'Sem permissão'}, status=403)

        if quantidade <= 0:
            return JsonResponse({'error': 'Quantidade inválida'}, status=400)

        if quantidade > produto.quantidade:
            return JsonResponse({'error': 'Quantidade maior que o estoque atual'}, status=400)

        # atualiza a quantidade
        produto.quantidade -= quantidade
        produto.save()

        # registra a movimentação
        from .models import Movimentacao
        Movimentacao.objects.create(
            produto=produto,
            usuario=request.user,
            quantidade=quantidade,  # sempre positivo
            tipo='saida',
            observacao=request.POST.get('observacao', '')
        )

        return JsonResponse({'success': True, 'nova_quantidade': produto.quantidade})

    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Quantidade inválida'}, status=400)


    
@login_required(login_url='login')
@user_passes_test(is_admin)
def movimentacoes(request):
    movs = Movimentacao.objects.select_related('produto','usuario').order_by('-data')

    # filtros
    usuario = request.GET.get('usuario')
    produto = request.GET.get('produto')
    tipo = request.GET.get('tipo')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if usuario:
        movs = movs.filter(usuario__username__icontains=usuario)
    if produto:
        movs = movs.filter(produto__nome__icontains=produto)
    if tipo:
        movs = movs.filter(tipo=tipo)
    if data_inicio:
        movs = movs.filter(data__date__gte=data_inicio)
    if data_fim:
        movs = movs.filter(data__date__lte=data_fim)

    return render(request, 'estoque/movimentacoes.html', {'movimentacoes': movs})

@login_required(login_url='login')
@user_passes_test(is_admin)
def exportar_movimentacoes(request):
    movs = Movimentacao.objects.select_related('produto','usuario').order_by('-data')

    # aplica os mesmos filtros do form
    usuario = request.GET.get('usuario')
    produto = request.GET.get('produto')
    tipo = request.GET.get('tipo')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if usuario:
        movs = movs.filter(usuario__username__icontains=usuario)
    if produto:
        movs = movs.filter(produto__nome__icontains=produto)
    if tipo:
        movs = movs.filter(tipo=tipo)
    if data_inicio:
        movs = movs.filter(data__date__gte=data_inicio)
    if data_fim:
        movs = movs.filter(data__date__lte=data_fim)

    # Cria CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="movimentacoes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Usuário', 'Produto', 'Tipo', 'Quantidade', 'Observação'])
    for mov in movs:
        writer.writerow([mov.data.strftime("%d/%m/%Y %H:%M"), mov.usuario.username, mov.produto.nome, mov.get_tipo_display(), mov.quantidade, mov.observacao])

    return response
     
@login_required(login_url='login')
@user_passes_test(is_admin)
def dashboard_graficos(request):
    """
    Tela de gráficos do Admin com total de produtos por setor.
    """
    # Consulta: total de produtos por setor
    produtos_por_setor = (
        Produto.objects
        .values('setor_responsavel__name')
        .annotate(total=Sum('quantidade'))
        .order_by('setor_responsavel__name')
    )

    # Gerando dados para Chart.js
    chart_labels = [p['setor_responsavel__name'] for p in produtos_por_setor]
    chart_data = [p['total'] for p in produtos_por_setor]

    context = {
    'produtos_por_setor': produtos_por_setor,
    'labels_json': json.dumps(chart_labels),
    'data_json': json.dumps(chart_data),
}


    return render(request, 'estoque/graficos.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def exportar_graficos_csv(request):
    """
    Exporta os dados de produtos por setor em CSV.
    """
    produtos_por_setor = Produto.objects.values('setor_responsavel__name') \
                                        .annotate(total=Sum('quantidade')) \
                                        .order_by('setor_responsavel__name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estoque_setores.csv"'

    writer = csv.writer(response)
    writer.writerow(['Setor', 'Total de Produtos'])

    for item in produtos_por_setor:
        writer.writerow([item['setor_responsavel__name'], item['total']])

    return response

def listar_produtos(request):
    produtos = Produto.objects.all()
    setores = Group.objects.all()  # pega todos os setores
    return render(request, 'estoque/listar_produtos.html', {
        'produtos': produtos,
        'setores': setores,
    })