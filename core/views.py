from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages

def home(request):
    """
    Vista de la página principal de la EEB Antonio Ante.
    """
    context = {
        'titulo': 'Inicio | EEB Antonio Ante',
    }
    return render(request, 'core/home.html', context)

def user_logout(request):
    """
    Cierra la sesión del usuario de forma segura y redirige al inicio.
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente en el portal institucional.')
    return redirect('core:home')
