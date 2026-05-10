# Vyranos — SaaS landing page + réservation pour commerces locaux

## Vision
SaaS qui permet à n'importe quel commerce local (restaurant, salon, coach, artisan...) de créer en quelques minutes :
1. Une landing page personnalisée
2. Un système de réservation intégré

URL publique style `vyranos.app/<slug>`.

## Modèle économique
- **69€/mois** (prix fixe, plus de promo)
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
    main.py                     # / et /demo/* (données démo hardcodées)
    auth.py                     # /signup /login /logout
    onboarding.py               # /onboarding/step1..5
    dashboard.py                # /dashboard/*
    billing.py                  # /billing/* + webhook Stripe
    public.py                   # /<slug> /<slug>/booking /<slug>/confirmation/<id>
    admin.py                    # /admin/* (panneau superadmin, auth session séparée)
  templates/
    base.html                   # Layout de base avec toasts flash (auto-dismiss 4s)
    index.html                  # Landing SaaS (69€/mois, 5 templates cliquables)
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
- custom_domain (nullable, unique) — domaine personnalisé ex: `moncommerce.be`

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
- `/` → landing (69€/mois, 5 templates cliquables)
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
- `/dashboard/domaine` → configurer un domaine personnalisé (CNAME + instructions)

### Côté public (page client)
- `/<slug>` → landing page du commerce (template sélectionné)
- `/<slug>/booking` → réservation (calendrier JS, créneaux générés, form)
- `/<slug>/confirmation/<id>` → confirmation RDV

### Admin (superadmin)
- `/admin/login` → auth session (email + mdp depuis .env)
- `/admin` → dashboard avec 5 stats : clients inscrits, abonnés actifs, en essai, réservations totales, MRR (abonnés × 69€)
- `/admin/client/<id>` → détail client + ses réservations + bouton suspendre/réactiver
- `/admin/client/<id>/toggle` POST → bascule `is_active` (Flask-Login bloque immédiatement)

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

### Prix
- 69€/mois fixe, essai gratuit 7 jours, engagement 6 mois après 1er paiement
- Les services publics affichent "Sur rendez-vous" à la place du prix (le prix reste en base pour usage interne)

### Gestion trial expiré
- `before_request` dans `dashboard_bp` : redirige vers `/billing` si `is_subscribed()` retourne False
- S'applique à toutes les routes `/dashboard/*` automatiquement

### Domaines personnalisés
- Champ `custom_domain` sur Business (ex: `moncommerce.be`)
- `CustomDomainMiddleware` dans `__init__.py` : intercepte les requêtes WSGI, détecte le host, réécrit le path vers `/<slug>/...` avant que Flask route
- Le client configure un CNAME vers `vyranos.app` chez son registrar
- Louis doit ajouter le domaine manuellement dans Railway (Settings → Networking → Custom Domain) pour activer le HTTPS

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

## Variables d'environnement

### Local (.env)
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

### Prod (Railway → service web → Variables)
```
SECRET_KEY=vyranos-super-secret-key-2026
DATABASE_URL=postgresql://postgres:oTZZjNhiyrtmTyJiFlfEbpQIQbiZBypH@postgres.railway.internal:5432/railway
ADMIN_EMAIL=blankaertlouis@outlook.com
ADMIN_PASSWORD=Bl@nk@3rt
FLASK_ENV=production
STRIPE_* → à ajouter quand Stripe sera configuré
```

## Lancer en dev
```bash
venv/bin/python run.py
# → http://localhost:5001
```

## Kill le port
```bash
lsof -ti :5001 | xargs kill -9
```

## TablePlus
- **Local** : SQLite → `/Users/louisblankaert/Desktop/vyranos/instance/vyranos.db`
- **Prod** : PostgreSQL → host `switchback.proxy.rlwy.net`, port `36896`, user `postgres`, db `railway`

### Supprimer un user en prod (contraintes FK)
Ordre : `reservation` → `blocage` → `service` → `business` → `subscription` → `user`

## Déploiement Railway
- Service Flask + plugin PostgreSQL
- Gunicorn via `Procfile`, Python 3.12 via `.python-version`
- Chaque `git push` → redéploiement automatique
- Domaine custom : Settings → Networking → Custom Domain → `vyranos.app` (à faire quand domaine acheté)

## Lancer Claude Code
Toujours lancer depuis `/Users/louisblankaert/Desktop/vyranos/`.

## À faire
1. **Stripe** — abonnement récurrent, webhook, activation compte après trial
2. **Uploads prod** — logos/covers éphémères sur Railway → migrer vers Cloudinary ou S3
3. **Domaine `vyranos.app`** — acheter + configurer CNAME dans Railway
4. **Emails transactionnels (Resend)** — 3 emails à implémenter :
   - Notif à Louis quand un nouveau client s'inscrit
   - Confirmation de réservation au client final
   - Notification au commerçant quand il a un nouveau RDV

## Fait
- ✅ Gestion trial expiré — dashboard bloqué automatiquement
- ✅ Domaines personnalisés — CNAME + WSGI middleware + page dashboard
- ✅ Admin enrichi — MRR, stats trial, suspendre/réactiver compte
- ✅ Prix 69€/mois partout, engagement 6 mois, plus de promo
