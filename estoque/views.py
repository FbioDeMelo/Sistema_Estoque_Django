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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator

# -------------------- View do Estoque --------------------
@login_required(login_url='login')
def index(request):
    user_groups = request.user.groups.all()
    is_admin = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser
    pertence_geral = request.user.groups.filter(name__iexact='Geral').exists()

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
        'pertence_geral': pertence_geral,   # ✅ agora o template sabe se o usuário é do Geral
        'total_produtos': total_produtos,
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

    # 🔹 monta o contexto principal
    context = {
        'form': form,
    }
    # 🔹 adiciona o contexto do sidebar
    context.update(get_sidebar_context(request))

    return render(request, 'estoque/adicionar_usuario.html', context)
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

    # só deixa acessar se o usuário tem permissão
    if not is_admin and setor not in [g.name for g in user_groups]:
        return redirect('index')

    if is_admin and setor == 'todos':
        produtos_qs = Produto.objects.all().order_by('nome')
    else:
        produtos_qs = Produto.objects.filter(setor_responsavel__name=setor).order_by('nome')

    # === PAGINAÇÃO ===
    paginator = Paginator(produtos_qs, 15)  # 15 produtos por página
    page_number = request.GET.get('page')
    produtos_page = paginator.get_page(page_number)

    # Prepara hub_info para a sidebar
    if is_admin:
        setores = Group.objects.all()
    else:
        setores = user_groups

    hub_info = []
    for s in setores:
        produtos_setor_qs = Produto.objects.filter(setor_responsavel=s)
        hub_info.append({
            'nome_setor': s.name,
            'total_produtos': produtos_setor_qs.count()
        })

    context = {
        'produtos': produtos_page,  # <<< passa a página, não o queryset inteiro
        'setor': setor,
        'is_admin': is_admin,
        'hub_info': hub_info,
        'setores': setores,  # para o filtro do template
    }
    return render(request, 'estoque/produtos.html', context)


# -------------------- View para Gerenciar Usuários --------------------
@login_required(login_url='login')
@user_passes_test(is_admin)
def gerenciar_usuarios(request):
    # ------------------ POST (edição via modal) ------------------
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        usuario = get_object_or_404(User, id=user_id)

        # Atualiza campos diretamente do POST
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')

        senha = request.POST.get('senha')
        if senha:
            usuario.set_password(senha)  # altera apenas se preenchido

        usuario.save()

        # Atualiza grupo
        grupo_id = request.POST.get('grupo')
        grupo = get_object_or_404(Group, id=grupo_id)
        usuario.groups.clear()
        usuario.groups.add(grupo)

        return redirect('gerenciar_usuarios')

    # ------------------ GET (exibir lista) ------------------
    usuarios = User.objects.all()
    grupos = Group.objects.all()

    # Contexto para sidebar (mantendo padrão)
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


from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)  # remove a sessão do usuário
    return redirect('login')  # redireciona para a tela de login
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
    movs = Movimentacao.objects.select_related('produto', 'usuario').order_by('-data')

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

    # === PAGINAÇÃO ===
    paginator = Paginator(movs, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    movs_page = paginator.get_page(page_number)

    # === INFO EXTRA PARA A SIDEBAR ===
    hub_info = [{'nome_setor': g.name} for g in Group.objects.all()]

    # Passa para o template
    return render(request, 'estoque/movimentacoes.html', {
        'movimentacoes': movs_page,
        'setores': Group.objects.all(),
        'hub_info': hub_info,
        'is_admin': request.user.is_superuser,  # controla a exibição dos links de admin
    })

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
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta, date, time
import calendar
from .models import Produto, Movimentacao, Setor 
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')  # redireciona para login se não for admin
def dashboard_graficos(request, periodo='all'):
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

    hoje = timezone.now().date()

    # Determina data inicial e função de trunc
    if periodo == "7":
        inicio = hoje - timedelta(days=7)
        trunc_func = TruncDay
    elif periodo == "30":
        inicio = hoje - timedelta(days=30)
        trunc_func = TruncDay
    elif periodo == "mes":
        inicio = hoje.replace(day=1)
        trunc_func = TruncDay
    else:
        inicio = None
        trunc_func = TruncMonth

    def aplicar_filtro(queryset, campo="data"):
        if inicio:
            filtro = {f"{campo}__gte": inicio}
            return queryset.filter(**filtro)
        return queryset

    def gerar_dados_linha(queryset, campo="data"):
        queryset = queryset.filter(**{f"{campo}__isnull": False})
        qs = aplicar_filtro(queryset, campo=campo)\
            .annotate(data_trunc=trunc_func(campo))\
            .values("data_trunc")\
            .annotate(total=Count("id"))\
            .order_by("data_trunc")

        labels, valores = [], []
        for item in qs:
            data = item["data_trunc"]
            if periodo == "all":
                labels.append(f"{calendar.month_abbr[data.month]} {data.year}")
            else:
                labels.append(data.strftime("%d/%m"))
            valores.append(item["total"])
        return labels, valores

    moviment_label, moviment_values = gerar_dados_linha(Movimentacao.objects)

    # Contexto para o template (sidebar precisa de is_admin e hub_info)
    context = {
        'is_admin': True,  # porque esse view é só admin
        'hub_info': Setor.objects.all(),  # ou a lógica para os setores do usuário
        'produtos_por_setor': produtos_por_setor,
        'labels_json': json.dumps(chart_labels),
        'data_json': json.dumps(chart_data),
        'movimentacoes_valores': json.dumps(moviment_values),
        'movimentacoes_meses': json.dumps(moviment_label),
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

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Protocolo, Produto
from .forms import ProtocoloForm

@login_required(login_url='login')
def protocolo_create(request):
    if request.method == 'POST':
        form = ProtocoloForm(request.POST)
        if form.is_valid():
            protocolo = form.save(commit=False)
            produto = protocolo.item

            if isinstance(produto, str):
                try:
                    produto = Produto.objects.get(nome=produto)
                except Produto.DoesNotExist:
                    messages.error(request, "Produto não encontrado!")
                    return redirect('protocolo_create')

            if produto.quantidade > 0:
                produto.quantidade -= 1
                produto.save()
            else:
                messages.error(request, "Estoque insuficiente!")
                return redirect('protocolo_create')

            protocolo.item = produto
            protocolo.save()
            messages.success(request, 'Item registrado e debitado do estoque!')
            return redirect('protocolo_create')
    else:
        form = ProtocoloForm()

    # ✅ adiciona contexto da sidebar
    context = {'form': form}
    context.update(get_sidebar_context(request))

    return render(request, 'estoque/protocolo.html', context)


from .forms import ColaboradorForm

def colaborador_create(request):
    if request.method == 'POST':
        form = ColaboradorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Colaborador cadastrado com sucesso!')
            return redirect('colaborador_create')
    else:
        form = ColaboradorForm()

    # ✅ adiciona contexto da sidebar
    context = {'form': form}
    context.update(get_sidebar_context(request))

    return render(request, 'estoque/colaborador_form.html', context)


from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Colaborador, Protocolo

from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def lista_colaboradores(request):
    query = request.GET.get('q', '')
    colaboradores = Colaborador.objects.all()

    if query:
        colaboradores = colaboradores.filter(
            Q(nome__icontains=query) | Q(codigo__icontains=query)
        )

    paginator = Paginator(colaboradores, 15)
    page_number = request.GET.get('page')
    colaboradores_page = paginator.get_page(page_number)

    # ✅ adiciona contexto da sidebar
    context = {'colaboradores': colaboradores_page}
    context.update(get_sidebar_context(request))

    return render(request, 'estoque/lista_colaboradores.html', context)


def exportar_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    protocolos = Protocolo.objects.filter(colaborador=colaborador)

    conteudo = f"Colaborador: {colaborador.nome} ({colaborador.codigo})\n\nItens vinculados:\n"
    for p in protocolos:
        conteudo += f"- {p.item} | Patrimônio: {p.patrimonio} | Data: {p.data.strftime('%d/%m/%Y %H:%M')}\n"

    response = HttpResponse(conteudo, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="colaborador_{colaborador.id}.txt"'
    return response
# Função que retorna os dados comuns da sidebar
def get_sidebar_context(request):
    user_groups = request.user.groups.all()
    is_admin = request.user.groups.filter(name='ADMIN').exists() or request.user.is_superuser
    pertence_geral = request.user.groups.filter(name__iexact='Geral').exists()

    if is_admin:
        setores = Group.objects.all()
    else:
        setores = user_groups

    hub_info = []
    for s in setores:
        total_produtos = Produto.objects.filter(setor_responsavel=s).count()
        hub_info.append({
            'nome_setor': s.name,
            'total_produtos': total_produtos
        })

    return {
        'is_admin': is_admin,
        'hub_info': hub_info,
        'pertence_geral': pertence_geral
    }

from django.http import JsonResponse
from .models import Colaborador, Produto

def buscar_colaboradores(request):
    termo = request.GET.get('q', '')
    colaboradores = Colaborador.objects.filter(nome__icontains=termo)[:10]

    results = [{"id": c.id, "nome": c.nome, "codigo": c.codigo} for c in colaboradores]
    return JsonResponse(results, safe=False)

def buscar_produtos(request):
    termo = request.GET.get('q', '')
    produtos = Produto.objects.filter(nome__icontains=termo)[:10]

    results = [{"id": p.id, "nome": p.nome, "quantidade": p.quantidade} for p in produtos]
    return JsonResponse(results, safe=False)