"""
URL configuration for copa2026 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from torneio.views import (
    GrupoViewSet,
    TecnicoViewSet,
    SelecaoViewSet,
    JogadorViewSet,
    JogoViewSet,
    EventoJogoViewSet
)

router = DefaultRouter()

router.register(r'grupos', GrupoViewSet)
router.register(r'tecnicos', TecnicoViewSet)
router.register(r'selecoes', SelecaoViewSet)
router.register(r'jogadores', JogadorViewSet)
router.register(r'jogos', JogoViewSet)
router.register(r'eventos-jogo', EventoJogoViewSet)


schema_view = get_schema_view(
    openapi.Info(
        title="Copa 2026 API",
        default_version='v1',
        description="API da Copa do Mundo 2026",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        'copa2026_api/',
        include(router.urls)
    ),

    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
]