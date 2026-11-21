from datetime import date
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from smtplib import SMTPException
from email.mime.image import MIMEImage
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.staticfiles import finders
from .models import (
    NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto,
    PerfilUsuario, CifrasInstitucionales, OfertaAcademica,
)
from .forms import (
    NoticiaComunicadoForm, FotoGaleriaForm, DocentePersonalForm, MensajeContactoForm,
    UsuarioCrearForm, UsuarioEditarForm, PerfilPropioEditarForm, CambiarPasswordForm,
    ConsultaSeguimientoForm, CifrasInstitucionalesForm,
)

def es_administrador(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return hasattr(user, 'perfil') and user.perfil.rol == 'administrador'


def rol_usuario(user):
    if not user.is_authenticated:
        return ''
    try:
        return user.perfil.rol
    except PerfilUsuario.DoesNotExist:
        return ''


def puede_gestionar_noticias(user):
    return es_administrador(user) or rol_usuario(user) in ('noticias', 'dece')


def puede_gestionar_galeria(user):
    return es_administrador(user) or rol_usuario(user) == 'galeria'


def puede_gestionar_personal(user):
    return es_administrador(user)


def puede_atender_consultas(user):
    return es_administrador(user)


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
            consulta = form_contacto.save()
            correo_configurado = all((
                settings.CONTACT_EMAIL_TO,
                settings.EMAIL_HOST,
                settings.EMAIL_HOST_USER,
                settings.EMAIL_HOST_PASSWORD,
                settings.DEFAULT_FROM_EMAIL,
            ))

            if correo_configurado:
                asunto = f"Nueva consulta #{consulta.pk} | EEB Antonio Ante"
                contenido = (
                    "Se recibi\u00f3 una nueva consulta en el sitio institucional.\n\n"
                    f"Ticket: #{consulta.pk}\n"
                    f"Nombre: {consulta.nombre}\n"
                    f"Tel\u00e9fono: {consulta.telefono}\n"
                    f"Correo: {consulta.email}\n"
                    f"Nivel de inter\u00e9s: {consulta.get_nivel_interes_display()}\n\n"
                    f"Consulta:\n{consulta.mensaje or 'Solicitud de informaci\u00f3n.'}\n\n"
                    "La consulta tambi\u00e9n est\u00e1 guardada en el panel de gesti\u00f3n."
                )

                try:
                    html_contenido = render_to_string(
                        "core/emails/consulta_notificacion.html",
                        {
                            "consulta": consulta,
                            "panel_url": request.build_absolute_uri(
                                f"{reverse('core:consultas_list')}?estado=pendiente"
                            ),
                        },
                    )
                    email = EmailMultiAlternatives(
                        subject=asunto,
                        body=contenido,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[settings.CONTACT_EMAIL_TO],
                        reply_to=[consulta.email],
                    )
                    email.attach_alternative(html_contenido, "text/html")
                    logo_path = finders.find("img/logo_antonio_ante.jpg")
                    if logo_path:
                        with open(logo_path, "rb") as logo_file:
                            logo = MIMEImage(logo_file.read())
                        logo.add_header("Content-ID", "<escudo-antonio-ante>")
                        logo.add_header(
                            "Content-Disposition",
                            "inline",
                            filename="escudo-antonio-ante.jpg",
                        )
                        email.attach(logo)
                    email.send(fail_silently=False)

                except (SMTPException, OSError, TimeoutError, ValueError) as exc:
                    messages.warning(
                        request,
                        'Su consulta quedó guardada en el panel, pero no se pudo enviar el correo. La secretaría podrá verla desde el panel de gestión.',
                    )
                else:
                    messages.success(
                        request,
                        'Su consulta fue enviada al correo institucional y quedó registrada en el panel de gestión.',
                    )
            else:
                messages.warning(
                    request,
                    'Su consulta qued\u00f3 guardada en el panel de gesti\u00f3n. El env\u00edo al correo institucional a\u00fan no est\u00e1 configurado.',
                )
            return redirect('core:home')
    else:
        form_contacto = MensajeContactoForm()

    noticias = NoticiaComunicado.objects.filter(destacado=True)[:6]
    aviso_importante = NoticiaComunicado.objects.filter(
        destacado=True, tipo='urgente'
    ).first()
    galeria = FotoGaleria.objects.filter(activa=True)[:8]
    personal_activo = list(DocentePersonal.objects.filter(activo=True))
    cifras_institucionales = CifrasInstitucionales.objects.filter(pk=1).first()
    total_estudiantes = getattr(cifras_institucionales, 'total_estudiantes', None)
    hoy = timezone.localdate()
    fecha_fundacion = date(1965, 9, 4)
    anos_institucion = hoy.year - fecha_fundacion.year - (
        (hoy.month, hoy.day) < (fecha_fundacion.month, fecha_fundacion.day)
    )
    autoridades = [persona for persona in personal_activo if persona.es_autoridad]
    docentes_matutina = [
        persona for persona in personal_activo if 'matutina' in persona.jornadas_asignadas
    ]
    docentes_vespertina = [
        persona for persona in personal_activo if 'vespertina' in persona.jornadas_asignadas
    ]
    dece_personal = [persona for persona in personal_activo if persona.esta_en_dece]
    ofertas_imagenes = {oferta.nivel: oferta for oferta in OfertaAcademica.objects.all()}
    archivos_estaticos = ('about_campus', 'inicial', 'elemental', 'media', 'superior')
    versiones_imagenes = {}
    for nombre in archivos_estaticos:
        ruta = finders.find(f'img/{nombre}.jpg')
        if ruta:
            stat = os.stat(ruta)
            versiones_imagenes[nombre] = f'{stat.st_mtime_ns}-{stat.st_size}'

    context = {
        'titulo': 'Inicio | EEB Antonio Ante',
        'noticias': noticias,
        'aviso_importante': aviso_importante,
        'galeria': galeria,
        'autoridades': autoridades,
        'docentes_matutina': docentes_matutina,
        'docentes_vespertina': docentes_vespertina,
        'dece_personal': dece_personal,
        'total_estudiantes': total_estudiantes,
        'tiene_total_estudiantes': total_estudiantes is not None,
        'total_docentes_publico': sum(
            1 for persona in personal_activo if 'docente' in persona.funciones_asignadas
        ),
        'anos_institucion': anos_institucion,
        'form_contacto': form_contacto,
        'ofertas_imagenes': ofertas_imagenes,
        'versiones_imagenes': versiones_imagenes,
    }
    return render(request, 'core/home.html', context)


def galeria_publica(request):
    """Muestra a los visitantes las fotografías activas de la institución."""
    categorias = FotoGaleria.CATEGORIA_CHOICES
    categoria = request.GET.get('categoria', '').strip()
    categorias_validas = {valor for valor, _ in categorias}
    if categoria not in categorias_validas:
        categoria = ''

    fotos = FotoGaleria.objects.filter(activa=True)
    if categoria:
        fotos = fotos.filter(categoria=categoria)

    page_obj = Paginator(fotos, 12).get_page(request.GET.get('page'))
    return render(request, 'core/galeria_publica.html', {
        'fotos': page_obj.object_list,
        'page_obj': page_obj,
        'categorias': categorias,
        'categoria_activa': categoria,
        'total_fotos': page_obj.paginator.count,
    })


def noticia_publica(request, pk):
    """Muestra el comunicado completo que la persona seleccionó en la portada."""
    noticia = NoticiaComunicado.objects.filter(pk=pk, destacado=True).first()
    if noticia is None:
        messages.info(request, 'Este comunicado ya no está disponible. Aquí puedes ver los comunicados vigentes.')
        return redirect(f"{reverse('core:home')}#noticias")
    return render(request, 'core/noticia_publica.html', {'noticia': noticia})


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
    rol = rol_usuario(request.user)
    es_admin = es_administrador(request.user)
    puede_noticias = es_admin or rol in ('noticias', 'dece')
    puede_galeria = es_admin or rol == 'galeria'
    puede_personal = es_admin
    puede_consultas = es_admin

    noticias = NoticiaComunicado.objects.all()
    if rol == 'dece' and not es_admin:
        noticias = noticias.filter(tipo='dece')

    total_noticias = noticias.count() if puede_noticias else 0
    total_fotos = FotoGaleria.objects.count() if puede_galeria else 0
    total_docentes = DocentePersonal.objects.count() if puede_personal else 0
    pendientes_consultas = MensajeContacto.objects.filter(leido=False) if puede_consultas else MensajeContacto.objects.none()
    total_mensajes = pendientes_consultas.count()
    consultas_vencidas = pendientes_consultas.filter(fecha_seguimiento__lte=timezone.now()).count()
    total_usuarios = User.objects.count() if es_admin else 0

    ultimas_noticias = noticias[:5] if puede_noticias else NoticiaComunicado.objects.none()
    ultimas_fotos = FotoGaleria.objects.all()[:4] if puede_galeria else FotoGaleria.objects.none()
    ultimas_consultas = pendientes_consultas.order_by('prioridad', 'fecha_seguimiento')[:5]

    context = {
        'rol_panel': 'Administrador' if es_admin else dict(PerfilUsuario.ROLES_CHOICES).get(rol, 'Personal'),
        'puede_gestionar_noticias': puede_noticias,
        'puede_gestionar_galeria': puede_galeria,
        'puede_gestionar_personal': puede_personal,
        'puede_atender_consultas': puede_consultas,
        'puede_gestionar_usuarios': es_admin,
        'total_noticias': total_noticias,
        'total_fotos': total_fotos,
        'total_docentes': total_docentes,
        'total_mensajes': total_mensajes,
        'consultas_vencidas': consultas_vencidas,
        'total_usuarios': total_usuarios,
        'ultimas_noticias': ultimas_noticias,
        'ultimas_fotos': ultimas_fotos,
        'ultimas_consultas': ultimas_consultas,
    }
    return render(request, 'core/dashboard/index.html', context)


@login_required
@user_passes_test(puede_gestionar_personal)
@verificar_primer_cambio_clave
def cifras_editar(request):
    """Permite a administración actualizar manualmente la matrícula pública."""
    cifras, _ = CifrasInstitucionales.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = CifrasInstitucionalesForm(request.POST, instance=cifras)
        if form.is_valid():
            form.save()
            messages.success(request, 'La cifra de estudiantes se actualizó correctamente.')
            return redirect('core:cifras_editar')
    else:
        form = CifrasInstitucionalesForm(instance=cifras)
    return render(request, 'core/dashboard/cifras_form.html', {'form': form})


# --- Gestión de Noticias y Comunicados ---
@login_required
@user_passes_test(puede_gestionar_noticias)
@verificar_primer_cambio_clave
def noticia_list(request):
    noticias = NoticiaComunicado.objects.all()
    if rol_usuario(request.user) == 'dece' and not es_administrador(request.user):
        noticias = noticias.filter(tipo='dece')
    return render(request, 'core/dashboard/noticia_list.html', {'noticias': noticias})

@login_required
@user_passes_test(puede_gestionar_noticias)
@verificar_primer_cambio_clave
def noticia_create(request):
    solo_dece = rol_usuario(request.user) == 'dece' and not es_administrador(request.user)
    if request.method == 'POST':
        form = NoticiaComunicadoForm(request.POST, request.FILES)
        if solo_dece:
            form.fields['tipo'].choices = [('dece', 'Aviso DECE')]
        if form.is_valid():
            noticia = form.save(commit=False)
            if solo_dece:
                noticia.tipo = 'dece'
            noticia.autor = request.user
            noticia.save()
            messages.success(request, 'Noticia o comunicado publicado exitosamente.')
            return redirect('core:noticia_list')
    else:
        form = NoticiaComunicadoForm()
        if solo_dece:
            form.fields['tipo'].choices = [('dece', 'Aviso DECE')]
    return render(request, 'core/dashboard/noticia_form.html', {'form': form, 'titulo_accion': 'Publicar Nuevo Comunicado'})

@login_required
@user_passes_test(puede_gestionar_noticias)
@verificar_primer_cambio_clave
def noticia_edit(request, pk):
    noticias = NoticiaComunicado.objects.all()
    solo_dece = rol_usuario(request.user) == 'dece' and not es_administrador(request.user)
    if solo_dece:
        noticias = noticias.filter(tipo='dece')
    noticia = get_object_or_404(noticias, pk=pk)
    if request.method == 'POST':
        form = NoticiaComunicadoForm(request.POST, request.FILES, instance=noticia)
        if solo_dece:
            form.fields['tipo'].choices = [('dece', 'Aviso DECE')]
        if form.is_valid():
            form.instance.tipo = 'dece' if solo_dece else form.instance.tipo
            form.save()
            messages.success(request, 'Publicación actualizada correctamente.')
            return redirect('core:noticia_list')
    else:
        form = NoticiaComunicadoForm(instance=noticia)
        if solo_dece:
            form.fields['tipo'].choices = [('dece', 'Aviso DECE')]
    return render(request, 'core/dashboard/noticia_form.html', {'form': form, 'titulo_accion': 'Editar Publicación', 'noticia': noticia})

@login_required
@user_passes_test(puede_gestionar_noticias)
@verificar_primer_cambio_clave
def noticia_delete(request, pk):
    noticias = NoticiaComunicado.objects.all()
    if rol_usuario(request.user) == 'dece' and not es_administrador(request.user):
        noticias = noticias.filter(tipo='dece')
    noticia = get_object_or_404(noticias, pk=pk)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Publicación eliminada correctamente.')
        return redirect('core:noticia_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': noticia, 'tipo': 'Noticia / Comunicado', 'cancel_url': 'core:noticia_list'})


# --- Gestión de Galería Fotográfica ---
@login_required
@user_passes_test(puede_gestionar_galeria)
@verificar_primer_cambio_clave
def galeria_list(request):
    fotos = FotoGaleria.objects.all()
    return render(request, 'core/dashboard/galeria_list.html', {'fotos': fotos})

@login_required
@user_passes_test(puede_gestionar_galeria)
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
@user_passes_test(puede_gestionar_galeria)
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
@user_passes_test(puede_gestionar_personal)
@verificar_primer_cambio_clave
def docente_list(request):
    docentes = DocentePersonal.objects.all()
    return render(request, 'core/dashboard/docente_list.html', {'docentes': docentes})

@login_required
@user_passes_test(puede_gestionar_personal)
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
@user_passes_test(puede_gestionar_personal)
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
@user_passes_test(puede_gestionar_personal)
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
@user_passes_test(puede_atender_consultas)
@verificar_primer_cambio_clave
def consultas_list(request):
    # Los tickets atendidos se eliminan; limpia los que quedaron en el historial anterior.
    MensajeContacto.objects.filter(leido=True).delete()
    pendientes = MensajeContacto.objects.filter(leido=False)
    consultas = pendientes.order_by('prioridad', 'fecha_seguimiento', 'fecha_envio')
    for consulta in consultas:
        consulta.seguimiento_form = ConsultaSeguimientoForm(
            instance=consulta, prefix=f'ticket-{consulta.pk}'
        )

    context = {
        'consultas': consultas,
        'total_pendientes': pendientes.count(),
        'total_vencidas': pendientes.filter(fecha_seguimiento__lte=timezone.now()).count(),
        'prioridad_choices': MensajeContacto.PRIORIDAD_CHOICES,
    }
    return render(request, 'core/dashboard/consultas_list.html', context)

@login_required
@user_passes_test(puede_atender_consultas)
@verificar_primer_cambio_clave
@require_POST
def consulta_toggle(request, pk):
    consulta = get_object_or_404(MensajeContacto, pk=pk, leido=False)
    ticket_id = consulta.pk
    consulta.delete()
    messages.success(request, f'El ticket #{ticket_id} fue eliminado al marcarlo como atendido.')
    return redirect('core:consultas_list')


@login_required
@user_passes_test(puede_atender_consultas)
@verificar_primer_cambio_clave
@require_POST
def consulta_actualizar(request, pk):
    consulta = get_object_or_404(MensajeContacto, pk=pk, leido=False)
    form = ConsultaSeguimientoForm(request.POST, instance=consulta, prefix=f'ticket-{consulta.pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Seguimiento del ticket #{consulta.pk} actualizado.')
    else:
        messages.error(request, 'No se pudo guardar. Revisa la prioridad y la fecha del recordatorio.')
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
    credenciales_creadas = request.session.pop('usuario_credenciales_creadas', None)
    return render(request, 'core/dashboard/usuario_list.html', {
        'usuarios': usuarios,
        'credenciales_creadas': credenciales_creadas,
    })


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
            request.session['usuario_credenciales_creadas'] = {
                'username': user.username,
                'password': form.cleaned_data['cedula'],
                'nombre': f"{form.cleaned_data['nombres']} {form.cleaned_data['apellidos']}",
            }
            messages.success(request, f'La cuenta de @{user.username} fue creada.')
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
