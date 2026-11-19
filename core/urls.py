from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Vista pública principal
    path('', views.home, name='home'),

    # Autenticación
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Portal Institucional / Dashboard Post-Login
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gestión de Noticias y Comunicados
    path('dashboard/noticias/', views.noticia_list, name='noticia_list'),
    path('dashboard/noticias/crear/', views.noticia_create, name='noticia_create'),
    path('dashboard/noticias/<int:pk>/editar/', views.noticia_edit, name='noticia_edit'),
    path('dashboard/noticias/<int:pk>/eliminar/', views.noticia_delete, name='noticia_delete'),

    # Gestión de Galería Fotográfica
    path('dashboard/galeria/', views.galeria_list, name='galeria_list'),
    path('dashboard/galeria/subir/', views.galeria_create, name='galeria_create'),
    path('dashboard/galeria/<int:pk>/eliminar/', views.galeria_delete, name='galeria_delete'),

    # Gestión de Planta Docente y DECE
    path('dashboard/docentes/', views.docente_list, name='docente_list'),
    path('dashboard/docentes/registrar/', views.docente_create, name='docente_create'),
    path('dashboard/docentes/<int:pk>/editar/', views.docente_edit, name='docente_edit'),
    path('dashboard/docentes/<int:pk>/eliminar/', views.docente_delete, name='docente_delete'),

    # Consultas de Secretaría
    path('dashboard/consultas/', views.consultas_list, name='consultas_list'),
    path('dashboard/consultas/<int:pk>/atender/', views.consulta_toggle, name='consulta_toggle'),
]
