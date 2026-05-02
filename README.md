# Site da Igreja — Django

Site elegante e sofisticado para igrejas, desenvolvido com Django.

## Funcionalidades

- **Página Inicial** com Hero, versículo, eventos, ministérios e testemunhos
- **Eventos e Agenda** com categorias, filtros, destaque e detalhes
- **Sobre a Igreja** com ministérios e valores
- **Contato** com formulário e informações
- **Painel Admin** completo para gerenciar tudo sem programar
- Design **responsivo** e elegante (Cormorant Garamond + Jost)

## Como rodar

### 1. Instalar dependências

```bash
# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configurar o banco de dados

```bash
python manage.py migrate
```

### 3. Criar o superusuário (admin)

```bash
python manage.py createsuperuser
```

### 4. Rodar o servidor

```bash
python manage.py runserver
```

Acesse: http://localhost:8000

Painel Admin: http://localhost:8000/admin

---

## Personalizando o site

Acesse o **Admin** e configure:

### Configurações do Site
`Admin → Configurações Gerais → Configurações do Site`
- Nome da Igreja, slogan, logo
- Imagem de capa (Hero)
- Endereço, telefone, e-mail
- Links das redes sociais

### Eventos
`Admin → Eventos → Eventos`
- Crie eventos com título, data, local, imagem
- Defina categorias com cores personalizadas
- Marque eventos como "Destaque" para aparecer em evidência
- Configure recorrência (semanal, mensal etc.)

### Ministérios
`Admin → Configurações Gerais → Ministérios`
- Ícones usando classes Font Awesome (ex: `fa-music`, `fa-child`)

### Testemunhos
`Admin → Configurações Gerais → Testemunhos`
- Adicione testemunhos com foto opcional

---

## Estrutura do Projeto

```
church_project/
├── church_project/      # Configurações Django
│   ├── settings.py
│   └── urls.py
├── core/                # App principal
│   ├── models.py        # SiteSettings, Ministry, Testimony
│   ├── views.py
│   └── templates/core/
│       ├── base.html
│       ├── home.html
│       ├── about.html
│       └── contact.html
├── events/              # App de eventos
│   ├── models.py        # Event, Category
│   ├── views.py
│   └── templates/events/
│       ├── event_list.html
│       └── event_detail.html
├── static/
│   ├── css/style.css
│   └── js/main.js
├── media/               # Uploads de imagens
├── manage.py
└── requirements.txt
```

## Próximos Passos (Expandir)

- [ ] App de Blog / Devocionais
- [ ] Transmissão ao vivo (YouTube embed)
- [ ] Área de membros com login
- [ ] Doações online (integração PagSeguro/Stripe)
- [ ] Galeria de fotos
- [ ] Newsletter
