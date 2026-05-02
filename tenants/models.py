from django.db import models


class Igreja(models.Model):
    # ── Identificação ──────────────────────────────────────
    nome = models.CharField("Nome da Igreja", max_length=200)
    slug = models.SlugField(
        "Slug", unique=True,
        help_text="Usado na URL: minhagreja.seuapp.com.br"
    )
    dominio_proprio = models.CharField(
        "Domínio Próprio", max_length=253, blank=True,
        help_text="Ex: www.igrejadagraca.com.br (sem https://)"
    )

    # ── Status ─────────────────────────────────────────────
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # ── Plano ──────────────────────────────────────────────
    PLANO_CHOICES = [
        ('basic', 'Básico'),
        ('pro',   'Pro'),
        ('trial', 'Trial'),
    ]
    plano = models.CharField(
        "Plano", max_length=10,
        choices=PLANO_CHOICES, default='trial'
    )
    trial_ate = models.DateField(
        "Trial até", null=True, blank=True,
        help_text="Data de expiração do período de teste"
    )

    class Meta:
        verbose_name = "Igreja"
        verbose_name_plural = "Igrejas"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def get_host(self, base_domain='seuapp.com.br'):
        """Retorna o host principal desta igreja."""
        if self.dominio_proprio:
            return self.dominio_proprio
        return f"{self.slug}.{base_domain}"