from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

class VistaInicioTests(TestCase):
    def test_redirige_si_no_autenticado(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/usuarios/iniciar-sesion/", response.url)

    def test_renderiza_para_usuario_autenticado(self):
        user = get_user_model().objects.create_user(email="user@test.com", password="secret")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
