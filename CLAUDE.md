# Vyranos — SaaS landing page + réservation pour commerces locaux

## Vision
SaaS qui permet à n'importe quel commerce local (restaurant, salon, coach, artisan...) de créer en quelques minutes :
1. Une landing page personnalisée
2. Un système de réservation intégré

URL publique style `vyranos.app/<slug>`.

## Modèle économique
- Promo 29€/mois jusqu'au 30 mai 2026, puis 69€/mois (géré dynamiquement dans `main.py`)
- Essai gratuit 7 jours
- Cible : commerces locaux belges/français

## Stack
- Python 3 + Flask + SQLAlchemy
- SQLite en dev (`instance/vyranos.db`), PostgreSQL en prod
- Jinja2 + Tailwind CSS via CDN
- Stripe (abonnement récurrent)
- Flask-Login + bcrypt (auth commerçant)
- Session Flask (auth admin séparée)
- Google Fonts : Inter, Playfair Display, Lora, Outfit, DM Sans

## Structure du projet
```
run.py                          # Point d'entrée (port 5001 — 5000 pris par AirPlay sur Mac)
app/
  __init__.py                   # Factory Flask, init db + login_manager
  models.py                     # User, Business, Service, Reservation, Blocage, Subscription
  routes/
    main.py                     # / et /demo/* (données démo hardcodées + prix dynamique)
    auth.py                     # /signup /login /logout
    onboarding.py               # /onboarding/step1..5
    dashboard.py                # /dashboard/*
    billing.py                  # /billing/* + webhook Stripe
    public.py                   # /<slug> /<slug>/booking /<slug>/confirmation/<id>
    admin.py                    # /admin/* (panneau superadmin, auth session séparée)
  templates/
    base.html                   # Layout de base avec toasts flash (auto-dismiss 4s)
    index.html                  # Landing SaaS (prix dynamique, 5 templates cliquables)
    demo.html                   # Page choix des 5 templates avec aperçu
    auth/                       # signup.html, login.html
    onboarding/                 # layout.html, step1..5.html
    dashboard/                  # layout.html (responsive hamburger) + pages
      index.html                # Vue d'ensemble + prochains RDV
      business.html             # Infos commerce + upload logo/cover + suppression
      services.html             # CRUD services (toggle actif/inactif)
      horaires.html             # Horaires par jour + sélecteur creneau_step
      reservations.html         # Agenda visuel semaine (blocs colorés) + pauses
      template.html             # Choix parmi 5 templates (aperçu visuel)
    billing/index.html
    admin/                      # login.html, index.html, client.html
    public/
      booking.html              # Réservation : vrai calendrier JS + créneaux pilules
      confirmation.html
      templates/                # elegant, moderne, nature, minimal, premium
  static/uploads/               # Logos et covers uploadés
instance/vyranos.db           # Base SQLite (dev)
```

## Modèles de données

### User (le commerçant)
- email, password_hash, slug (unique), stripe_customer_id, is_active, trial_ends_at, created_at, onboarding_step

### Business (infos du commerce)
- user_id, nom, description, adresse, ville, telephone, email_contact, instagram, tiktok
- logo_url, cover_url, couleur_primaire (#hex), horaires (JSON), template, creneau_step (int, défaut 30)

### Service
- business_id, nom, description, duree_minutes, prix, actif

### Reservation
- business_id, service_id, prenom (required), nom (nullable), email (nullable), telephone
- date, creneau ("HH:MM"), statut ("confirmé"/"annulé"), created_at

### Blocage (pause manuelle)
- business_id, date, debut ("HH:MM"), fin ("HH:MM"), motif

### Subscription
- user_id, stripe_subscription_id, statut, current_period_end

## Pages

### Côté SaaS (public)
- `/` → landing (prix 29€ ou 69€ selon date, 5 templates cliquables)
- `/demo` → choix des 5 templates
- `/demo/<template>` → démo complète avec données fictives (elegant/moderne/minimal/nature/premium)
- `/signup` `/login` `/logout`
- `/onboarding/step1..5` → wizard 5 étapes
- `/billing` → gestion abonnement Stripe

### Dashboard (commerçant connecté)
- `/dashboard` → vue d'ensemble + 10 prochains RDV confirmés
- `/dashboard/business` → infos commerce + logo/cover (upload + suppression)
- `/dashboard/services` → CRUD services + toggle actif
- `/dashboard/horaires` → horaires par jour + intervalle entre créneaux (15/30/45/60/90 min)
- `/dashboard/reservations` → **agenda semaine visuel** + pauses/blocages
- `/dashboard/template` → choix parmi 5 templates avec aperçu

### Côté public (page client)
- `/<slug>` → landing page du commerce (template sélectionné)
- `/<slug>/booking` → réservation (calendrier JS, créneaux générés, form)
- `/<slug>/confirmation/<id>` → confirmation RDV

### Admin (superadmin)
- `/admin/login` → auth session (email + mdp depuis .env)
- `/admin` → liste tous les clients
- `/admin/client/<id>` → détail client + ses réservations

## Logique métier

### Génération des créneaux
- `generate_creneaux(business, service, day)` dans `public.py`
- Step configurable : `business.creneau_step` (défaut 30 min)
- Blocages : un créneau est bloqué si son **heure de début** tombe dans la plage du blocage (pas si sa durée déborde dedans)
- Réservations : détection de chevauchement complet (`slot_start < r_end AND slot_end > r_start`)

### Agenda dashboard
- Vue semaine avec navigation prev/next + "Aujourd'hui"
- Blocs colorés positionnés par JS (HOUR_PX=64, START_HOUR=7)
- Pauses affichées en hachuré gris
- Clic → panneau latéral d'édition/suppression

### Prix dynamique landing
- Avant le 30/05/2026 : badge promo + 29€ barré 69€
- Après le 30/05/2026 : 69€ sans badge

### Auth admin
- Séparée de Flask-Login (session['admin_logged_in'])
- Credentials dans .env : ADMIN_EMAIL, ADMIN_PASSWORD

## Templates disponibles (5)
Tous utilisent `--primary` (CSS variable) pour boutons/accents/prix. Couleur choisie par le client.

1. **Élégant** — fond sombre `#1e1e2e`, Cormorant Garamond. Démo : doré `#c9a84c`
2. **Moderne** — fond beige crème `#fdf6ec`, hero brun, wave SVG. Démo : brun `#8B4513`
3. **Minimal** — blanc épuré, Inter. Démo : noir `#111111`
4. **Nature** — beige organique `#faf7f2`, Lora italic, boutons pill. Démo : vert `#5c7a4e`
5. **Premium** — blanc, Outfit, deux colonnes hero. Démo : rouge `#c41e3a`

En mode démo (`is_demo=True`) : bannière couleur primaire + boutons → `/signup`.

## Variables d'environnement (.env)
```
SECRET_KEY=
DATABASE_URL=sqlite:///vyranos.db
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
ADMIN_EMAIL=blankaertlouis@outlook.com
ADMIN_PASSWORD=Bl@nk@3rt
```

## Lancer en dev
```bash
venv/bin/python run.py
# → http://localhost:5001
```

## Kill le port
```bash
lsof -ti :5001 | xargs kill -9
# ou Ctrl+C dans le terminal Flask
```

## TablePlus (DB)
Path SQLite : `/Users/louisblankaert/Desktop/vyranos/instance/vyranos.db`

> **Migration DB** : si `instance/localsite.db` existe encore (ancienne session), faire :
> ```bash
> rm instance/vyranos.db && mv instance/localsite.db instance/vyranos.db
> ```

## Lancer Claude Code
Toujours lancer depuis `/Users/louisblankaert/Desktop/vyranos/` (pas l'ancien chemin `localsite`).
Sans ça, le tool Bash ne fonctionne pas (répertoire de travail invalide).
