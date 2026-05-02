from django.http import HttpResponse
from .models import Igreja


class TenantMiddleware:
    """
    Detecta a igreja pelo host da requisição.
    Suporta subdomínio (igreja1.seuapp.com.br)
    e domínio próprio (www.igrejadagraca.com.br).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()  # remove porta se houver

        igreja = self._resolver_tenant(host)
        request.igreja = igreja  # disponível em todas as views e templates

        return self.get_response(request)

    def _resolver_tenant(self, host):
        # 1) Tenta domínio próprio
        try:
            return Igreja.objects.get(dominio_proprio=host, ativo=True)
        except Igreja.DoesNotExist:
            pass

        # 2) Tenta subdomínio (pega a primeira parte do host)
        partes = host.split('.')
        if len(partes) >= 2:
            slug = partes[0]
            # Ignora 'www' e 'localhost'
            if slug not in ('www', 'localhost', '127'):
                try:
                    return Igreja.objects.get(slug=slug, ativo=True)
                except Igreja.DoesNotExist:
                    pass

        # 3) Localhost / desenvolvimento — retorna a primeira igreja ativa
        #    ou None se não houver nenhuma ainda
        return Igreja.objects.filter(ativo=True).first()