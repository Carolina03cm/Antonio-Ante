from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import NoticiaComunicado, FotoGaleria, DocentePersonal, MensajeContacto
from .forms import NoticiaComunicadoForm, FotoGaleriaForm, DocentePersonalForm, MensajeContactoForm

def home(request):
    """
    Vista de la página principal pública de la EEB Antonio Ante.
    Muestra información dinámica desde la base de datos con fallback seguro.
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
    messages.info(request, 'Has cerrado sesión correctamente en el portal institucional.')
    return redirect('core:home')


# ==============================================================================
# MÓDULOS DE ACCESO DESPUÉS DEL LOGIN (PORTAL / DASHBOARD DE GESTIÓN)
# ==============================================================================

@login_required
def dashboard(request):
    """
    Panel de control principal post-login para docentes y administradores.
    """
    total_noticias = NoticiaComunicado.objects.count()
    total_fotos = FotoGaleria.objects.count()
    total_docentes = DocentePersonal.objects.count()
    total_mensajes = MensajeContacto.objects.filter(leido=False).count()

    ultimas_noticias = NoticiaComunicado.objects.all()[:5]
    ultimas_fotos = FotoGaleria.objects.all()[:4]
    ultimas_consultas = MensajeContacto.objects.all()[:5]

    context = {
        'total_noticias': total_noticias,
        'total_fotos': total_fotos,
        'total_docentes': total_docentes,
        'total_mensajes': total_mensajes,
        'ultimas_noticias': ultimas_noticias,
        'ultimas_fotos': ultimas_fotos,
        'ultimas_consultas': ultimas_consultas,
    }
    return render(request, 'core/dashboard/index.html', context)


# --- Gestión de Noticias y Comunicados ---
@login_required
def noticia_list(request):
    noticias = NoticiaComunicado.objects.all()
    return render(request, 'core/dashboard/noticia_list.html', {'noticias': noticias})

@login_required
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
def noticia_delete(request, pk):
    noticia = get_object_or_404(NoticiaComunicado, pk=pk)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Publicación eliminada correctamente.')
        return redirect('core:noticia_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': noticia, 'tipo': 'Noticia / Comunicado', 'cancel_url': 'core:noticia_list'})


# --- Gestión de Galería Fotográfica ---
@login_required
def galeria_list(request):
    fotos = FotoGaleria.objects.all()
    return render(request, 'core/dashboard/galeria_list.html', {'fotos': fotos})

@login_required
def galeria_create(request):
    if request.method == 'POST':
        form = FotoGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fotografía subida a la galería institucional.')
            return redirect('core:galeria_list')
    else:
        form = FotoGaleriaForm()
    return render(request, 'core/dashboard/galeria_form.html', {'form': form, 'titulo_accion': 'Subir Fotografía'})

@login_required
def galeria_delete(request, pk):
    foto = get_object_or_404(FotoGaleria, pk=pk)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Fotografía eliminada de la galería.')
        return redirect('core:galeria_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': foto, 'tipo': 'Fotografía de Galería', 'cancel_url': 'core:galeria_list'})


# --- Gestión de Docentes y Personal ---
@login_required
def docente_list(request):
    docentes = DocentePersonal.objects.all()
    return render(request, 'core/dashboard/docente_list.html', {'docentes': docentes})

@login_required
def docente_create(request):
    if request.method == 'POST':
        form = DocentePersonalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente o funcionario añadido a la nómina institucional.')
            return redirect('core:docente_list')
    else:
        form = DocentePersonalForm()
    return render(request, 'core/dashboard/docente_form.html', {'form': form, 'titulo_accion': 'Registrar Docente / Personal'})

@login_required
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
    return render(request, 'core/dashboard/docente_form.html', {'form': form, 'titulo_accion': 'Editar Docente / Personal', 'docente': docente})

@login_required
def docente_delete(request, pk):
    docente = get_object_or_404(DocentePersonal, pk=pk)
    if request.method == 'POST':
        docente.delete()
        messages.success(request, 'Docente retirado de la nómina.')
        return redirect('core:docente_list')
    return render(request, 'core/dashboard/confirm_delete.html', {'objeto': docente, 'tipo': 'Docente / Personal', 'cancel_url': 'core:docente_list'})


# --- Consultas Recibidas ---
@login_required
def consultas_list(request):
    consultas = MensajeContacto.objects.all()
    return render(request, 'core/dashboard/consultas_list.html', {'consultas': consultas})

@login_required
def consulta_toggle(request, pk):
    consulta = get_object_or_404(MensajeContacto, pk=pk)
    consulta.leido = not consulta.leido
    consulta.save()
    messages.success(request, f'Estado de consulta de {consulta.nombre} actualizado.')
    return redirect('core:consultas_list')
