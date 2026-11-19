from django.shortcuts import render

def home(request):
    """
    Vista de la página principal de la EEB Antonio Ante.
    """
    context = {
        'titulo': 'Inicio | EEB Antonio Ante',
    }
    return render(request, 'core/home.html', context)
