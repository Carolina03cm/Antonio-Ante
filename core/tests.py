from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import (
    DocentePersonal,
    FotoGaleria,
    MensajeContacto,
    NoticiaComunicado,
    PerfilUsuario,
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

    def test_contacto_valido_se_guarda_y_redirige(self):
        respuesta = self.client.post(
            reverse("core:home"),
            {"nombre": "Ana Pérez", "telefono": "0991234567", "mensaje": "Consulta de prueba"},
        )

        self.assertRedirects(respuesta, reverse("core:home"))
        self.assertEqual(MensajeContacto.objects.count(), 1)
        contacto = MensajeContacto.objects.get()
        self.assertEqual(contacto.nombre, "Ana Pérez")
        self.assertEqual(contacto.telefono, "0991234567")
        self.assertFalse(contacto.leido)

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

        respuesta = self.client.post(
            reverse("core:docente_create"),
            {
                "nombres": "María",
                "apellidos": "López",
                "cargo": "Docente tutora",
                "jornada": "matutina",
                "area": "Lengua",
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
                "cargo": "Directora",
                "jornada": "autoridades",
                "area": "Dirección",
                "orden": 1,
                "activo": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("core:docente_list"))
        docente.refresh_from_db()
        self.assertEqual(docente.cargo, "Directora")
        self.assertEqual(docente.jornada, "autoridades")

        respuesta = self.client.post(reverse("core:docente_delete", args=[docente.pk]))
        self.assertRedirects(respuesta, reverse("core:docente_list"))
        self.assertFalse(DocentePersonal.objects.exists())
