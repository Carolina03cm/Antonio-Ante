from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto, PerfilUsuario
from .forms import (
    NoticiaComunicadoForm, FotoGaleriaForm, DocentePersonalForm, MensajeContactoForm,
    UsuarioCrearForm, UsuarioEditarForm, PerfilPropioEditarForm, CambiarPasswordForm
)

def es_administrador(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return hasattr(user, 'perfil') and user.perfil.rol == 'administrador'


def verificar_primer_cambio_clave(view_func):
    """
    Decorador que obliga a cambiar la contraseña si el usuario tiene la bandera activada.
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'perfil') and request.user.perfil.debe_cambiar_password:
            messages.warning(request, 'Por seguridad institucional, debe establecer su propia contraseña en este primer ingreso.')
            return redirect('core:cambiar_password')
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    """
    Vista de la página principal pública de la EEB Antonio Ante.
    """
    if request.method == 'POST':
        form_contacto = MensajeContactoForm(request.POST)
        if form_contacto.is_valid():
            form_contacto.save()
            messages.success(request, 'Su consulta ha sido registrada exitosamente en secretaría.')
            return redirect('core:home')
    else:
        form_contacto = MensajeContactoForm()

    noticias = NoticiaComunicado.objects.filter(destacado=True)[:6]
    galeria = FotoGaleria.objects.filter(activa=True)[:8]
    autoridades = DocentePersonal.objects.filter(jornada='autoridades', activo=True)
    docentes_matutina = DocentePersonal.objects.filter(jornada='matutina', activo=True)
    docentes_vespertina = DocentePersonal.objects.filter(jornada='vespertina', activo=True)
    dece_personal = DocentePersonal.objects.filter(jornada='dece', activo=True)

    context = {
        'titulo': 'Inicio | EEB Antonio Ante',
        'noticias': noticias,
        'galeria': galeria,
        'autoridades': autoridades,
        'docentes_matutina': docentes_matutina,
        'docentes_vespertina': docentes_vespertina,
        'dece_personal': dece_personal,
        'form_contacto': form_contacto,
    }
    return render(request, 'core/home.html', context)


def user_logout(request):
    """
    Cierra la sesión del usuario de forma segura y redirige al inicio.
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('core:home')


# ==============================================================================
# CAMBIO DE CONTRASEÑA OBLIGATORIO / PRIMER INGRESO
# ==============================================================================

@login_required
def cambiar_password(request):
    """
    Obliga o permite al usuario cambiar su contraseña temporal por una definitiva.
    """
    if request.method == 'POST':
        form = CambiarPasswordForm(request.POST)
        if form.is_valid():
            nuevo = form.cleaned_data['nuevo_password']
            request.user.set_password(nuevo)
            request.user.save()

            if hasattr(request.user, 'perfil'):
                request.user.perfil.debe_cambiar_password = False
                request.user.perfil.save()

            update_session_auth_hash(request, request.user)
            messages.success(request, '¡Contraseña establecida con éxito! Ya puedes usar el portal.')
            return redirect('core:dashboard')
    else:
        form = CambiarPasswordForm()

    return render(request, 'core/dashboard/cambiar_password.html', {'form': form})


# ==============================================================================
# PERFIL PROPIO (EDITAR DATOS DEL ADMINISTRADOR / DOCENTE Y SU FOTO)
# ==============================================================================

@login_required
@verificar_primer_cambio_clave
def perfil_editar(request):
    """
    Permite al usuario (administrador o docente) actualizar sus propios nombres,
    apellidos, correo, cédula y foto de perfil.
    """
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PerfilPropioEditarForm(request.POST, request.FILES)
        if form.is_valid():
            nombres = form.cleaned_data['nombres'].strip()
            apellidos = form.cleaned_data['apellidos'].strip()
            cedula = form.cleaned_data.get('cedula', '').strip()
            email = form.cleaned_data.get('email', '').strip()

            request.user.first_name = nombres.split()[0] if nombres else ''
            request.user.last_name = apellidos.split()[0] if apellidos else ''
            request.user.email = email
            request.user.save()

            perfil.nombres = nombres
            perfil.apellidos = apellidos
            perfil.cedula = cedula
            if form.cleaned_data.get('foto'):
                perfil.foto = form.cleaned_data['foto']
            elif request.POST.get('eliminar_foto') == '1':
                perfil.foto.delete(save=False)
                perfil.foto = None
            perfil.save()

            messages.success(request, 'Sus datos y fotografía han sido actualizados con éxito.')
            return redirect('core:perfil_editar')
    else:
        initial = {
            'nombres': perfil.nombres or request.user.first_name,
            'apellidos': perfil.apellidos or request.user.last_name,
            'cedula': perfil.cedula,
            'email': request.user.email,
        }
        form = PerfilPropioEditarForm(initial=initial)

    return render(request, 'core/dashboard/perfil_form.html', {'form': form, 'perfil': perfil})


# ==============================================================================
# MÓDULOS DE ACCESO DESPUÉS DEL LOGIN (PORTAL / DASHBOARD DE GESTIÓN)
# ==============================================================================

@login_required
@verificar_primer_cambio_clave
def dashboard(request):
    """
    Panel de control principal post-login para docentes y administradores.
    """
    total_noticias = NoticiaComunicado.objects.count()
    total_fotos = FotoGaleria.objects.count()
    total_docentes = DocentePersonal.objects.count()
    total_mensajes = MensajeContacto.objects.filter(leido=False).count()
    total_usuarios = User.objects.count()

    ultimas_noticias = NoticiaComunicado.objects.all()[:5]
    ultimas_fotos = FotoGaleria.objects.all()[:4]
    ultimas_consultas = MensajeContacto.objects.all()[:5]

    context = {
        'total_noticias': total_noticias,
        'total_fotos': total_fotos,
        'total_docentes': total_docentes,
        'total_mensajes': total_mensajes,
        'total_usuarios': total_usuarios,
        'ultimas_noticias': ultimas_noticias,
        'ultimas_fotos': ultimas_fotos,
        'ultimas_consultas': ultimas_consultas,
    }
    return render(request, 'core/dashboard/index.html', context)


# --- Gestión de Noticias y Comunicados ---
@login_required
@verificar_primer_cambio_clave
def noticia_list(request):
    noticias = NoticiaComunicado.objects.all()
    return render(request, 'core/dashboard/noticia_list.html', {'noticias': noticias})

@login_required
@verificar_primer_cambio_clave
def noticia_create(request):
    if request.method == 'POST':
        form = NoticiaComunicadoForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.save()
            messages.success(request, 'Noticia o comunicado publicado exitosamente.')
            return redirect('core:noticia_list')
    else:
        form = NoticiaComunicadoForm()
    return render(request, 'core/dashboard/noticia_form.html', {'form': form, 'titulo_accion': 'Publicar Nuevo Comunicado'})

@login_required
@verificar_primer_cambio_clave
def noticia_edit(request, pk):
    noticia = get_object_or_404(NoticiaComunicado, pk=pk)
    if request.method == 'POST':
        form = NoticiaComunicadoForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publicación actualizada correctamente.')
            return redirect('core:noticia_list')
    else:
        form = NoticiaComunicadoForm(instance=noticia)
    return render(request, 'core/dashboard/noticia_form.html', {'form': form, 'titulo_accion': 'Editar Publicación', 'noticia': noticia})

@login_required
@verificar_primer_cambio_clave
def noticia_delete(request, pk):
    noticia = get_object_or_404(NoticiaComunicado, pk=pk)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Publicación eliminada correctamente.')
        return redirect('core:noticia_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': noticia, 'tipo': 'Noticia / Comunicado', 'cancel_url': 'core:noticia_list'})


# --- Gestión de Galería Fotográfica ---
@login_required
@verificar_primer_cambio_clave
def galeria_list(request):
    fotos = FotoGaleria.objects.all()
    return render(request, 'core/dashboard/galeria_list.html', {'fotos': fotos})

@login_required
@verificar_primer_cambio_clave
def galeria_create(request):
    if request.method == 'POST':
        form = FotoGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fotografía subida a la galería institucional.')
            return redirect('core:galeria_list')
    else:
        form = FotoGaleriaForm()
    return render(request, 'core/dashboard/galeria_form.html', {'form': form, 'titulo_accion': 'Subir Fotografías'})

@login_required
@verificar_primer_cambio_clave
def galeria_delete(request, pk):
    foto = get_object_or_404(FotoGaleria, pk=pk)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Fotografía eliminada de la galería.')
        return redirect('core:galeria_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': foto, 'tipo': 'Fotografía de Galería', 'cancel_url': 'core:galeria_list'})


# --- Gestión de Docentes y Autoridades ---
@login_required
@verificar_primer_cambio_clave
def docente_list(request):
    docentes = DocentePersonal.objects.all()
    return render(request, 'core/dashboard/docente_list.html', {'docentes': docentes})

@login_required
@verificar_primer_cambio_clave
def docente_create(request):
    if request.method == 'POST':
        form = DocentePersonalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente o funcionario añadido a la nómina institucional.')
            return redirect('core:docente_list')
    else:
        form = DocentePersonalForm()
    return render(request, 'core/dashboard/docente_form.html', {'form': form, 'titulo_accion': 'Registrar Docente / Autoridad'})

@login_required
@verificar_primer_cambio_clave
def docente_edit(request, pk):
    docente = get_object_or_404(DocentePersonal, pk=pk)
    if request.method == 'POST':
        form = DocentePersonalForm(request.POST, request.FILES, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos del docente actualizados correctamente.')
            return redirect('core:docente_list')
    else:
        form = DocentePersonalForm(instance=docente)
    return render(request, 'core/dashboard/docente_form.html', {'form': form, 'titulo_accion': 'Editar Docente / Autoridad', 'docente': docente})

@login_required
@verificar_primer_cambio_clave
def docente_delete(request, pk):
    docente = get_object_or_404(DocentePersonal, pk=pk)
    if request.method == 'POST':
        docente.delete()
        messages.success(request, 'Docente retirado de la nómina.')
        return redirect('core:docente_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': docente, 'tipo': 'Docente / Personal', 'cancel_url': 'core:docente_list'})


# --- Consultas Recibidas ---
@login_required
@verificar_primer_cambio_clave
def consultas_list(request):
    consultas = MensajeContacto.objects.all()
    return render(request, 'core/dashboard/consultas_list.html', {'consultas': consultas})

@login_required
@verificar_primer_cambio_clave
def consulta_toggle(request, pk):
    consulta = get_object_or_404(MensajeContacto, pk=pk)
    consulta.leido = not consulta.leido
    consulta.save()
    messages.success(request, f'Estado de consulta de {consulta.nombre} actualizado.')
    return redirect('core:consultas_list')


# ==============================================================================
# GESTIÓN DE USUARIOS Y ROLES (SOLO ADMINISTRADOR)
# ==============================================================================

@login_required
@user_passes_test(es_administrador)
@verificar_primer_cambio_clave
def usuario_list(request):
    """
    Lista todos los usuarios del sistema institucional y sus roles asignados.
    """
    usuarios = User.objects.all().select_related('perfil').order_by('-is_superuser', 'username')
    return render(request, 'core/dashboard/usuario_list.html', {'usuarios': usuarios})


@login_required
@user_passes_test(es_administrador)
@verificar_primer_cambio_clave
def usuario_create(request):
    """
    Crea un nuevo usuario institucional con username autogenerado (ej: amorans)
    y contraseña temporal igual a su cédula.
    """
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario institucional "@{user.username}" creado con éxito. Su clave inicial es la cédula.')
            return redirect('core:usuario_list')
    else:
        form = UsuarioCrearForm()

    return render(request, 'core/dashboard/usuario_form.html', {'form': form, 'titulo_accion': 'Crear Nuevo Usuario y Rol'})


@login_required
@user_passes_test(es_administrador)
@verificar_primer_cambio_clave
def usuario_edit(request, pk):
    """
    Permite al administrador editar los datos, rol y estado de un usuario.
    """
    user_obj = get_object_or_404(User, pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user_obj)

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, request.FILES)
        if form.is_valid():
            nombres = form.cleaned_data['nombres'].strip()
            apellidos = form.cleaned_data['apellidos'].strip()
            cedula = form.cleaned_data['cedula'].strip()
            email = form.cleaned_data.get('email', '').strip()
            rol = form.cleaned_data['rol']
            activo = form.cleaned_data.get('activo', True)

            user_obj.first_name = nombres.split()[0] if nombres else ''
            user_obj.last_name = apellidos.split()[0] if apellidos else ''
            user_obj.email = email
            user_obj.is_active = activo
            if rol == 'administrador':
                user_obj.is_staff = True
            user_obj.save()

            perfil.nombres = nombres
            perfil.apellidos = apellidos
            perfil.cedula = cedula
            perfil.rol = rol
            if form.cleaned_data.get('foto'):
                perfil.foto = form.cleaned_data['foto']
            elif request.POST.get('eliminar_foto') == '1':
                perfil.foto.delete(save=False)
                perfil.foto = None
            perfil.save()

            messages.success(request, f'Usuario @{user_obj.username} actualizado correctamente.')
            return redirect('core:usuario_list')
    else:
        initial = {
            'nombres': perfil.nombres or user_obj.first_name,
            'apellidos': perfil.apellidos or user_obj.last_name,
            'cedula': perfil.cedula,
            'email': user_obj.email,
            'rol': perfil.rol,
            'activo': user_obj.is_active
        }
        form = UsuarioEditarForm(initial=initial)

    return render(request, 'core/dashboard/usuario_form.html', {
        'form': form,
        'user_obj': user_obj,
        'perfil': perfil,
        'titulo_accion': f'Editar Usuario: @{user_obj.username}'
    })


@login_required
@user_passes_test(es_administrador)
@verificar_primer_cambio_clave
def usuario_reset_password(request, pk):
    """
    Restablece la contraseña de un usuario al número de cédula y le obliga a cambiarla.
    """
    user_obj = get_object_or_404(User, pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user_obj)

    cedula = perfil.cedula or '12345678'
    user_obj.set_password(cedula)
    user_obj.save()

    perfil.debe_cambiar_password = True
    perfil.save()

    messages.success(request, f'La contraseña de @{user_obj.username} fue restablecida a su cédula ({cedula}). Se le pedirá cambiarla al ingresar.')
    return redirect('core:usuario_list')


@login_required
@user_passes_test(es_administrador)
@verificar_primer_cambio_clave
def usuario_delete(request, pk):
    """
    Elimina un usuario (no permite eliminarse a sí mismo).
    """
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta de usuario.')
        return redirect('core:usuario_list')

    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'Usuario @{username} eliminado del sistema.')
        return redirect('core:usuario_list')

    return render(request, 'core/dashboard/confirm_delete.html', {
        'objeto': user_obj,
        'tipo': f'Usuario @{user_obj.username}',
        'cancel_url': 'core:usuario_list'
    })
