from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

class CustomLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("usuarios:dashboard")

@login_required
def dashboard(request):
    return render(request, "home.html")
