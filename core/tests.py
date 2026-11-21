from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import (
    DocentePersonal,
    FotoGaleria,
    MensajeContacto,
    NoticiaComunicado,
    PerfilUsuario,
    CifrasInstitucionales,
)


def imagen_png(nombre="prueba.png"):
    """Crea una imagen PNG válida en memoria para las pruebas de carga."""
    contenido = BytesIO()
    Image.new("RGB", (2, 2), color="blue").save(contenido, format="PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


class SitioPublicoTests(TestCase):
    def test_inicio_carga_correctamente(self):
        respuesta = self.client.get(reverse("core:home"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "core/home.html")
        self.assertContains(respuesta, 'name="email"')
        self.assertContains(respuesta, 'name="nivel_interes"')
        self.assertContains(respuesta, "Seleccione un nivel...")
        self.assertContains(respuesta, 'name="acepta_privacidad"')

    def test_cifras_publicas_muestran_matricula_personal_y_trayectoria(self):
        CifrasInstitucionales.objects.create(total_estudiantes=327)
        DocentePersonal.objects.create(
            nombres="Ana María", apellidos="Pérez Ruiz", funciones=["docente"],
            jornadas=["matutina"],
        )
        DocentePersonal.objects.create(
            nombres="Luis", apellidos="Vera Mora", funciones=["docente"],
            jornadas=["vespertina"], activo=False,
        )

        respuesta = self.client.get(reverse("core:home"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total_estudiantes"], 327)
        self.assertEqual(respuesta.context["total_docentes_publico"], 1)
        hoy = timezone.localdate()
        anos_esperados = hoy.year - 1965 - ((hoy.month, hoy.day) < (9, 4))
        self.assertEqual(respuesta.context["anos_institucion"], anos_esperados)
        self.assertContains(respuesta, 'id="cifras-institucionales"')
        self.assertContains(respuesta, 'data-count="327"')
        self.assertContains(respuesta, "Docentes activos")

    def test_matricula_pendiente_se_indica_sin_inventar_un_total(self):
        respuesta = self.client.get(reverse("core:home"))

        self.assertContains(respuesta, "Matrícula por actualizar")
        self.assertNotContains(respuesta, 'data-count="None"')

    def test_aviso_importante_destacado_se_muestra_en_ventana_emergente(self):
        aviso = NoticiaComunicado.objects.create(
            titulo="Inscripciones abiertas",
            tipo="urgente",
            resumen="Proceso de admisiones para nuevas familias.",
            contenido="Las inscripciones se realizarán en secretaría.",
            destacado=True,
        )
        NoticiaComunicado.objects.create(
            titulo="Aviso no destacado",
            tipo="urgente",
            resumen="No debe aparecer en la ventana emergente.",
            contenido="Borrador de prueba.",
            destacado=False,
        )

        respuesta = self.client.get(reverse("core:home"))

        self.assertEqual(respuesta.context["aviso_importante"], aviso)
        self.assertContains(respuesta, 'id="importantNoticeModal"')
        self.assertContains(respuesta, "Inscripciones abiertas")
        self.assertContains(respuesta, "Leer aviso completo")
        self.assertContains(respuesta, 'class="important-notice-icon"')
        self.assertContains(respuesta, "sessionStorage")
        self.assertContains(respuesta, "bootstrap.Modal")
        self.assertNotContains(respuesta, "Aviso no destacado")

    def test_persona_aparece_en_cada_jornada_y_cargo_asignado(self):
        persona = DocentePersonal.objects.create(
            nombres="María Elena",
            apellidos="López García",
            cargo="Tutora de 4to EGB",
            jornada="matutina",
            funciones=["docente", "tutor", "rector"],
            jornadas=["matutina"],
            asignaturas=["Lengua", "Matemática"],
        )

        respuesta = self.client.get(reverse("core:home"))

        self.assertIn(persona, respuesta.context["autoridades"])
        self.assertIn(persona, respuesta.context["docentes_matutina"])
        self.assertContains(respuesta, "flex-column align-items-center")
        self.assertContains(respuesta, "Rector/a")
        self.assertContains(respuesta, "Lengua, Matemática")

    def test_contacto_valido_se_guarda_y_redirige(self):
        respuesta = self.client.post(
            reverse("core:home"),
            {
                "nombre": "Ana Pérez",
                "telefono": "0991234567",
                "email": "ana@example.com",
                "nivel_interes": "5_egb",
                "mensaje": "Consulta de prueba",
                "acepta_privacidad": "on",
            },
        )

        self.assertRedirects(respuesta, reverse("core:home"))
        self.assertEqual(MensajeContacto.objects.count(), 1)
        contacto = MensajeContacto.objects.get()
        self.assertEqual(contacto.nombre, "Ana Pérez")
        self.assertEqual(contacto.telefono, "0991234567")
        self.assertEqual(contacto.email, "ana@example.com")
        self.assertEqual(contacto.nivel_interes, "5_egb")
        self.assertTrue(contacto.acepta_privacidad)
        self.assertFalse(contacto.leido)

    def test_contacto_no_se_guarda_sin_aceptar_uso_de_datos(self):
        respuesta = self.client.post(
            reverse("core:home"),
            {
                "nombre": "Ana Pérez",
                "telefono": "0991234567",
                "email": "ana@example.com",
                "nivel_interes": "5_egb",
                "mensaje": "Consulta de prueba",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(MensajeContacto.objects.count(), 0)
        self.assertFormError(
            respuesta.context["form_contacto"],
            "acepta_privacidad",
            "Este campo es obligatorio.",
        )

    def test_contacto_invalido_no_se_guarda(self):
        respuesta = self.client.post(
            reverse("core:home"),
            {"nombre": "", "telefono": "0991234567", "mensaje": "Consulta de prueba"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(MensajeContacto.objects.count(), 0)
        self.assertFormError(respuesta.context["form_contacto"], "nombre", "Este campo es obligatorio.")

    def test_comunicado_destacado_se_abre_completo_en_el_sitio(self):
        noticia = NoticiaComunicado.objects.create(
            titulo="Charla para las familias",
            tipo="dece",
            resumen="Charla para la prevención",
            contenido="Este es el contenido completo del comunicado.",
            destacado=True,
        )

        portada = self.client.get(reverse("core:home"))
        self.assertContains(portada, reverse("core:noticia_publica", args=[noticia.pk]))

        detalle = self.client.get(reverse("core:noticia_publica", args=[noticia.pk]))
        self.assertEqual(detalle.status_code, 200)
        self.assertTemplateUsed(detalle, "core/noticia_publica.html")
        self.assertContains(detalle, "Charla para las familias")
        self.assertContains(detalle, "Este es el contenido completo del comunicado.")

    def test_comunicado_no_disponible_regresa_a_la_lista_con_aviso(self):
        noticia = NoticiaComunicado.objects.create(
            titulo="Borrador no destacado",
            resumen="Resumen",
            contenido="Contenido",
            destacado=False,
        )

        respuesta = self.client.get(reverse("core:noticia_publica", args=[noticia.pk]), follow=True)

        self.assertRedirects(respuesta, f"{reverse('core:home')}#noticias")
        self.assertContains(respuesta, "Este comunicado ya no está disponible.")

    def test_comunicado_eliminado_regresa_a_la_lista_con_aviso(self):
        noticia = NoticiaComunicado.objects.create(
            titulo="Comunicado eliminado",
            resumen="Resumen",
            contenido="Contenido",
            destacado=True,
        )
        noticia_id = noticia.pk
        noticia.delete()

        respuesta = self.client.get(reverse("core:noticia_publica", args=[noticia_id]), follow=True)

        self.assertRedirects(respuesta, f"{reverse('core:home')}#noticias")
        self.assertContains(respuesta, "Este comunicado ya no está disponible.")


class AccesoPanelTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="docente", password="ClaveSegura123!")
        self.perfil = PerfilUsuario.objects.create(user=self.usuario, rol="docente")
        self.administrador = User.objects.create_user(username="admin", password="ClaveSegura123!")
        PerfilUsuario.objects.create(user=self.administrador, rol="administrador")

    def test_panel_requiere_inicio_de_sesion(self):
        respuesta = self.client.get(reverse("core:dashboard"))

        self.assertRedirects(
            respuesta,
            f"{reverse('core:login')}?next={reverse('core:dashboard')}",
            fetch_redirect_response=False,
        )

    def test_usuario_con_cambio_obligatorio_es_enviado_al_formulario(self):
        self.perfil.debe_cambiar_password = True
        self.perfil.save(update_fields=["debe_cambiar_password"])
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse("core:dashboard"))

        self.assertRedirects(respuesta, reverse("core:cambiar_password"), fetch_redirect_response=False)

    def test_solo_administrador_accede_a_gestion_de_usuarios(self):
        self.client.force_login(self.usuario)
        respuesta_docente = self.client.get(reverse("core:usuario_list"))
        self.assertEqual(respuesta_docente.status_code, 302)

        self.client.force_login(self.administrador)
        respuesta_admin = self.client.get(reverse("core:usuario_list"))
        self.assertEqual(respuesta_admin.status_code, 200)
        self.assertTemplateUsed(respuesta_admin, "core/dashboard/usuario_list.html")

    def test_solo_administrador_actualiza_matricula_institucional(self):
        self.client.force_login(self.usuario)
        respuesta_docente = self.client.get(reverse("core:cifras_editar"))
        self.assertEqual(respuesta_docente.status_code, 302)

        self.client.force_login(self.administrador)
        respuesta_formulario = self.client.get(reverse("core:cifras_editar"))
        self.assertEqual(respuesta_formulario.status_code, 200)
        self.assertTemplateUsed(respuesta_formulario, "core/dashboard/cifras_form.html")

        respuesta_guardado = self.client.post(
            reverse("core:cifras_editar"), {"total_estudiantes": "327"}
        )

        self.assertRedirects(respuesta_guardado, reverse("core:cifras_editar"))
        self.assertEqual(CifrasInstitucionales.objects.get(pk=1).total_estudiantes, 327)

    def test_rol_noticias_ve_solo_sus_herramientas(self):
        self.perfil.rol = "noticias"
        self.perfil.save(update_fields=["rol"])
        self.client.force_login(self.usuario)

        self.assertEqual(self.client.get(reverse("core:noticia_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:galeria_list")).status_code, 302)
        self.assertEqual(self.client.get(reverse("core:docente_list")).status_code, 302)
        self.assertEqual(self.client.get(reverse("core:consultas_list")).status_code, 302)

        respuesta = self.client.get(reverse("core:dashboard"))
        self.assertContains(respuesta, "Noticias y comunicados")
        self.assertNotContains(respuesta, "Fotos de la escuela")
        self.assertNotContains(respuesta, "Mensajes de las familias")

    def test_rol_galeria_ve_solo_sus_herramientas(self):
        self.perfil.rol = "galeria"
        self.perfil.save(update_fields=["rol"])
        self.client.force_login(self.usuario)

        self.assertEqual(self.client.get(reverse("core:galeria_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:noticia_list")).status_code, 302)
        self.assertEqual(self.client.get(reverse("core:docente_list")).status_code, 302)

        respuesta = self.client.get(reverse("core:dashboard"))
        self.assertContains(respuesta, "Fotos registradas")
        self.assertNotContains(respuesta, "Noticias y comunicados")

    def test_rol_dece_solo_gestiona_avisos_dece(self):
        noticia_general = NoticiaComunicado.objects.create(
            titulo="Aviso general", resumen="Resumen", contenido="Contenido", tipo="noticia"
        )
        noticia_dece = NoticiaComunicado.objects.create(
            titulo="Taller DECE", resumen="Resumen", contenido="Contenido", tipo="dece"
        )
        self.perfil.rol = "dece"
        self.perfil.save(update_fields=["rol"])
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse("core:noticia_list"))
        self.assertContains(respuesta, "Taller DECE")
        self.assertNotContains(respuesta, "Aviso general")
        self.assertEqual(
            self.client.get(reverse("core:noticia_edit", args=[noticia_general.pk])).status_code,
            404,
        )
        form_respuesta = self.client.get(reverse("core:noticia_create"))
        self.assertEqual(
            list(form_respuesta.context["form"].fields["tipo"].choices),
            [("dece", "Aviso DECE")],
        )


class GestionTicketsTests(TestCase):
    def setUp(self):
        self.administrador = User.objects.create_user(
            username="admin_tickets", password="ClaveSegura123!"
        )
        PerfilUsuario.objects.create(user=self.administrador, rol="administrador")
        self.client.force_login(self.administrador)

    def crear_ticket(self, nombre, **datos):
        valores = {
            "nombre": nombre,
            "telefono": "0960172899",
            "mensaje": "Consulta de prueba",
        }
        valores.update(datos)
        return MensajeContacto.objects.create(**valores)

    def test_atender_mueve_el_ticket_al_historial_y_sale_de_pendientes(self):
        pendiente = self.crear_ticket(
            "Familia pendiente",
            email="familia@example.com",
            nivel_interes="5_egb",
        )
        atendido = self.crear_ticket("Familia atendida", leido=True)

        bandeja = self.client.get(reverse("core:consultas_list"))
        self.assertEqual(bandeja.context["estado_activo"], "pendiente")
        self.assertContains(bandeja, f"Ticket #{pendiente.pk}")
        self.assertContains(bandeja, "familia@example.com")
        self.assertContains(bandeja, "5.º de EGB")
        self.assertNotContains(bandeja, f"Ticket #{atendido.pk}")

        respuesta = self.client.post(
            reverse("core:consulta_toggle", args=[pendiente.pk]), follow=True
        )
        self.assertRedirects(
            respuesta,
            f"{reverse('core:consultas_list')}?estado=pendiente",
        )
        self.assertContains(respuesta, "No hay tickets pendientes")
        self.assertTrue(MensajeContacto.objects.get(pk=pendiente.pk).leido)

        historial = self.client.get(reverse("core:consultas_list"), {"estado": "atendido"})
        self.assertContains(historial, f"Ticket #{pendiente.pk}")
        self.assertContains(historial, f"Ticket #{atendido.pk}")

        respuesta_get = self.client.get(reverse("core:consulta_toggle", args=[pendiente.pk]))
        self.assertEqual(respuesta_get.status_code, 405)

    def test_prioridad_y_fecha_de_seguimiento_se_guardan_y_avisan_si_vencen(self):
        ticket = self.crear_ticket("Familia urgente")
        fecha_recordatorio = timezone.localtime(timezone.now() - timedelta(hours=1))
        respuesta = self.client.post(
            reverse("core:consulta_actualizar", args=[ticket.pk]),
            {
                f"ticket-{ticket.pk}-prioridad": str(MensajeContacto.PRIORIDAD_CHOICES[0][0]),
                f"ticket-{ticket.pk}-fecha_seguimiento": fecha_recordatorio.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertRedirects(
            respuesta,
            f"{reverse('core:consultas_list')}?estado=pendiente",
            fetch_redirect_response=False,
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.prioridad, 1)

        bandeja = self.client.get(reverse("core:consultas_list"))
        self.assertEqual(bandeja.context["total_vencidas"], 1)
        self.assertContains(bandeja, "Recordatorio vencido")

        panel = self.client.get(reverse("core:dashboard"))
        self.assertContains(panel, "Recordatorio vencido")
        self.assertContains(panel, "requiere seguimiento")


class CreacionUsuarioTests(TestCase):
    def setUp(self):
        self.administrador = User.objects.create_user(
            username="admin_creacion", password="ClaveSegura123!"
        )
        PerfilUsuario.objects.create(user=self.administrador, rol="administrador")
        self.client.force_login(self.administrador)

    def datos_usuario(self, **cambios):
        datos = {
            "nombres": "María Elena",
            "apellidos": "Pérez Ruiz",
            "cedula": "0923456789",
            "email": "",
            "rol": "docente",
        }
        datos.update(cambios)
        return datos

    def test_no_permite_crear_usuario_con_un_solo_apellido(self):
        respuesta = self.client.post(
            reverse("core:usuario_create"),
            self.datos_usuario(apellidos="Pérez"),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFormError(
            respuesta.context["form"],
            "apellidos",
            "Escribe los dos apellidos: paterno y materno.",
        )
        self.assertEqual(User.objects.count(), 1)

    def test_muestra_credenciales_para_copiar_una_sola_vez(self):
        respuesta_creacion = self.client.post(
            reverse("core:usuario_create"), self.datos_usuario()
        )

        self.assertRedirects(
            respuesta_creacion,
            reverse("core:usuario_list"),
            fetch_redirect_response=False,
        )
        usuario_creado = User.objects.get(username="mperezr")
        self.assertTrue(usuario_creado.check_password("0923456789"))

        lista = self.client.get(reverse("core:usuario_list"))
        self.assertContains(lista, 'id="createdUsername"')
        self.assertContains(lista, 'value="mperezr"')
        self.assertContains(lista, 'id="createdPassword"')
        self.assertContains(lista, 'value="0923456789"')
        self.assertContains(lista, "Copiar ambos")
        self.assertNotContains(lista, "Cédula (Clave Inicial)")

        lista_actualizada = self.client.get(reverse("core:usuario_list"))
        self.assertNotContains(lista_actualizada, 'id="createdPassword"')
        self.assertNotContains(lista_actualizada, "0923456789")


class GestionContenidoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="editor", password="ClaveSegura123!")
        self.perfil = PerfilUsuario.objects.create(user=self.usuario, rol="noticias")
        self.client.force_login(self.usuario)

        self.directorio_media = TemporaryDirectory()
        self.addCleanup(self.directorio_media.cleanup)
        override = self.settings(MEDIA_ROOT=self.directorio_media.name)
        override.enable()
        self.addCleanup(override.disable)

    def test_noticia_se_crea_edita_y_elimina(self):
        respuesta = self.client.post(
            reverse("core:noticia_create"),
            {
                "titulo": "Reunión de familias",
                "tipo": "noticia",
                "resumen": "Información para las familias",
                "contenido": "Contenido de prueba",
                "destacado": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("core:noticia_list"))
        noticia = NoticiaComunicado.objects.get()
        self.assertEqual(noticia.autor, self.usuario)
        self.assertEqual(noticia.titulo, "Reunión de familias")

        respuesta = self.client.post(
            reverse("core:noticia_edit", args=[noticia.pk]),
            {
                "titulo": "Reunión actualizada",
                "tipo": "comunicado",
                "resumen": "Nuevo resumen",
                "contenido": "Contenido actualizado",
                "destacado": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("core:noticia_list"))
        noticia.refresh_from_db()
        self.assertEqual(noticia.titulo, "Reunión actualizada")
        self.assertEqual(noticia.tipo, "comunicado")

        respuesta = self.client.post(reverse("core:noticia_delete", args=[noticia.pk]))
        self.assertRedirects(respuesta, reverse("core:noticia_list"))
        self.assertFalse(NoticiaComunicado.objects.exists())

    def test_galeria_se_crea_y_elimina(self):
        self.perfil.rol = "galeria"
        self.perfil.save(update_fields=["rol"])
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("core:galeria_create"),
            {
                "titulo": "Acto cívico",
                "categoria": "civico",
                "descripcion": "Actividad escolar",
                "activa": "on",
                "imagen": imagen_png(),
            },
        )
        self.assertRedirects(respuesta, reverse("core:galeria_list"))
        foto = FotoGaleria.objects.get()
        self.assertTrue(foto.imagen.name.startswith("galeria/"))
        self.assertTrue(foto.activa)

        respuesta = self.client.post(reverse("core:galeria_delete", args=[foto.pk]))
        self.assertRedirects(respuesta, reverse("core:galeria_list"))
        self.assertFalse(FotoGaleria.objects.exists())

    def test_docente_se_crea_edita_y_elimina(self):
        self.perfil.rol = "administrador"
        self.perfil.save(update_fields=["rol"])
        self.client.force_login(self.usuario)

        formulario = self.client.get(reverse("core:docente_create"))
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, "assignment-checkboxes")
        self.assertContains(formulario, "grid-template-columns")

        respuesta = self.client.post(
            reverse("core:docente_create"),
            {
                "nombres": "María",
                "apellidos": "López",
                "cargo": "Docente tutora",
                "funciones": ["docente", "tutor"],
                "jornadas": ["matutina"],
                "asignaturas": "Lengua, Matemática",
                "orden": 1,
                "activo": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("core:docente_list"))
        docente = DocentePersonal.objects.get()
        self.assertEqual(docente.nombre_completo, "María López")

        respuesta = self.client.post(
            reverse("core:docente_edit", args=[docente.pk]),
            {
                "nombres": "María",
                "apellidos": "López García",
                "cargo": "Rectora",
                "funciones": ["docente", "rector", "tutor"],
                "jornadas": ["autoridades", "matutina"],
                "asignaturas": "Lengua, Matemática, Ciencias Naturales",
                "orden": 1,
                "activo": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("core:docente_list"))
        docente.refresh_from_db()
        self.assertEqual(docente.cargo, "Rectora")
        self.assertEqual(docente.jornada, "autoridades")
        self.assertEqual(docente.funciones, ["docente", "rector", "tutor"])
        self.assertEqual(docente.jornadas, ["autoridades", "matutina"])
        self.assertEqual(docente.asignaturas, ["Lengua", "Matemática", "Ciencias Naturales"])

        respuesta = self.client.post(reverse("core:docente_delete", args=[docente.pk]))
        self.assertRedirects(respuesta, reverse("core:docente_list"))
        self.assertFalse(DocentePersonal.objects.exists())
