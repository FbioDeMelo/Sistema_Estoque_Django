from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Login
    path('', auth_views.LoginView.as_view(
        template_name='estoque/login.html'
    ), name='login'),

    # Logout (redireciona para login depois de sair)
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Hub de setores
    path('estoque/', views.index, name='index'),

    # Adicionar usuários/produtos
    path('adicionar_usuario/', views.adicionar_usuario, name='adicionar_usuario'),
    path('adicionar_produto/', views.adicionar_produto, name='adicionar_produto'),

    # Produtos detalhados por setor
    path('produtos/<str:setor>/', views.produtos_setor, name='produtos_setor'),

    # Usuários
    path('gerenciar_usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),

    # Estoque / movimentações
    path('retirar_item/<int:produto_id>/', views.retirar_item, name='retirar_item'),
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('movimentacoes/exportar/', views.exportar_movimentacoes, name='exportar_movimentacoes'),

    # Gráficos
    path('graficos/', views.dashboard_graficos, name='dashboard_graficos'),
    path('exportar_graficos/', views.exportar_graficos_csv, name='exportar_graficos_csv'),

    # Protocolo
    path('protocolo/', views.protocolo_create, name='protocolo_create'),

    # Colaboradores
    path("colaboradores/", views.lista_colaboradores, name="lista_colaboradores"),
    path("colaborador/<int:colaborador_id>/exportar/", views.exportar_colaborador, name="exportar_colaborador"),
    path("colaborador/adicionar/", views.colaborador_create, name="colaborador_create"),

    # Busca
    path("buscar_colaboradores/", views.buscar_colaboradores, name="buscar_colaboradores"),
    path("buscar_produtos/", views.buscar_produtos, name="buscar_produtos"),
    path('verifica_patrimonio/', views.verifica_patrimonio, name='verifica_patrimonio'),
    path("patrimonios/", views.lista_patrimonios, name="lista_patrimonios"),

]

# Para servir arquivos estáticos em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
