from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Login
    path('', auth_views.LoginView.as_view(
        template_name='estoque/login.html'
    ), name='login'),

    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Hub de setores
    path('estoque/', views.index, name='index'),

    # Adicionar usuários/produtos
    path('adicionar_usuario/', views.adicionar_usuario, name='adicionar_usuario'),
    path('adicionar_produto/', views.adicionar_produto, name='adicionar_produto'),

    # Produtos detalhados por setor
    path('produtos/<str:setor>/', views.produtos_setor, name='produtos_setor'),
    path('gerenciar_usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
    path('retirar_item/<int:produto_id>/', views.retirar_item, name='retirar_item'),
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('movimentacoes/exportar/', views.exportar_movimentacoes, name='exportar_movimentacoes'),
    path('graficos/', views.dashboard_graficos, name='dashboard_graficos'),
    path('exportar_graficos/', views.exportar_graficos_csv, name='exportar_graficos_csv'),

]

