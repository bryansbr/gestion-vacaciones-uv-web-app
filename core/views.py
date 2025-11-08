from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# ==========================================================
# CONSTANTES
# ==========================================================
HOME_TEMPLATE = "home.html"

@login_required
def home(request):
    return render(request, HOME_TEMPLATE)
