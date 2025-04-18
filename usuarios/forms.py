from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "Correo electrónico o contraseña incorrectos. Por favor, verifique sus credenciales.",
        'inactive': "Esta cuenta está inactiva. Contacte al administrador.",
    }
