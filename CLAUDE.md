# Vyranos — Sites sur mesure pour commerces locaux

## Vision
Service de création de sites web sur mesure pour commerces locaux. Louis crée chaque site manuellement pour ses clients. Chaque site inclut :
1. Une landing page personnalisée
2. Un système de réservation intégré

URL publique style `vyranos.app/<slug>`.

## Modèle économique
- Sites sur mesure — tarif sur rendez-vous
- Pas de self-service, pas d'abonnement Stripe
- Cible : commerces locaux belges/français

## Stack
- Python 3 + Flask + SQLAlchemy
- SQLite en dev (`instance/vyranos.db`), PostgreSQL en prod
- Jinja2 + Tailwind CSS via CDN
- Flask-Login + bcrypt (auth commerçant)
- Session Flask (auth admin séparée)
- Google Fonts : Inter

## Structure du projet
```
run.py                          # Point d'entrée (port 5001 — 5000 pris par AirPlay sur Mac)
app/
  __init__.py                   # Factory Flask, init db + login_manager + CustomDomainMiddleware
  models.py                     # User, Business, Service, Reservation, Blocage
  routes/
    main.py                     # / uniquement
    auth.py                     # /signup /login /logout
    dashboard.py                # /dashboard/*
    public.py                   # /<slug> /<slug>/booking /<slug>/confirmation/<id>
    admin.py                    # /admin/* (panneau superadmin, auth session séparée)
  templates/
    base.html                   # Layout de base avec toasts flash (auto-dismiss 4s)
    index.html                  # Landing SaaS (offre sur mesure, CTA email)
    auth/                       # signup.html, login.html
    dashboard/                  # layout.html (responsive hamburger) + pages
      index.html                # Vue d'ensemble + prochains RDV + services actifs
      business.html             # Infos commerce + upload logo/cover + suppression
      services.html             # CRUD services (toggle actif/inactif)
      horaires.html             # Horaires par jour + sélecteur creneau_step
      reservations.html         # Agenda visuel semaine (blocs colorés) + pauses
      domaine.html              # Configurer un domaine personnalisé
    admin/                      # login.html, index.html, client.html
    public/
      landing.html              # Page publique unique du commerce (design épuré, couleur_primaire)
      booking.html              # Réservation : calendrier JS + créneaux pilules
      confirmation.html
  static/uploads/               # Logos et covers uploadés
instance/vyranos.db             # Base SQLite (dev)
```

## Modèles de données

### User (le commerçant)
- email, password_hash, slug (unique), is_active, created_at

### Business (infos du commerce)
- user_id, nom, description, adresse, ville, telephone, email_contact, instagram, tiktok
- logo_url, cover_url, couleur_primaire (#hex), horaires (JSON), creneau_step (int, défaut 30)
- custom_domain (nullable, unique) — domaine personnalisé ex: `moncommerce.be`

### Service
- business_id, nom, description, duree_minutes, prix, actif

### Reservation
- business_id, service_id, prenom (required), nom (nullable), email (nullable), telephone
- date, creneau ("HH:MM"), statut ("confirmé"/"annulé"), created_at

### Blocage (pause manuelle)
- business_id, date, debut ("HH:MM"), fin ("HH:MM"), motif

## Pages

### Côté SaaS (public)
- `/` → landing (offre sur mesure, CTA vers email Louis)
- `/signup` `/login` `/logout`

### Dashboard (commerçant connecté)
- `/dashboard` → vue d'ensemble + 10 prochains RDV confirmés + nb services actifs
- `/dashboard/business` → infos commerce + couleur_primaire + logo/cover (upload + suppression)
- `/dashboard/services` → CRUD services + toggle actif
- `/dashboard/horaires` → horaires par jour + intervalle entre créneaux (15/30/45/60/90 min)
- `/dashboard/reservations` → **agenda semaine visuel** + pauses/blocages
- `/dashboard/domaine` → configurer un domaine personnalisé (CNAME + instructions)

### Côté public (page client)
- `/<slug>` → landing page du commerce (`public/landing.html`, utilise `couleur_primaire`)
- `/<slug>/booking` → réservation (calendrier JS, créneaux générés, form)
- `/<slug>/confirmation/<id>` → confirmation RDV

### Admin (superadmin)
- `/admin/login` → auth session (email + mdp depuis .env)
- `/admin` → dashboard : clients inscrits, comptes actifs, domaines perso, réservations totales
- `/admin/client/<id>` → détail client + ses réservations + bouton suspendre/réactiver + gestion domaine
- `/admin/client/<id>/toggle` POST → bascule `is_active`
- `/admin/client/<id>/domaine` POST → définit/retire le domaine personnalisé

## Logique métier

### Génération des créneaux
- `generate_creneaux(business, service, day)` dans `public.py`
- Step configurable : `business.creneau_step` (défaut 30 min)
- Blocages : un créneau est bloqué si son **heure de début** tombe dans la plage du blocage
- Réservations : détection de chevauchement complet (`slot_start < r_end AND slot_end > r_start`)

### Agenda dashboard
- Vue semaine avec navigation prev/next + "Aujourd'hui"
- Blocs colorés positionnés par JS (HOUR_PX=64, START_HOUR=7)
- Pauses affichées en hachuré gris
- Clic → panneau latéral d'édition/suppression

### Page publique
- Template unique `public/landing.html`
- Utilise la CSS variable `--primary` issue de `business.couleur_primaire`
- Services affichent "Sur rendez-vous" (le prix reste en base pour usage interne)

### Domaines personnalisés
- Champ `custom_domain` sur Business (ex: `moncommerce.be`)
- `CustomDomainMiddleware` dans `__init__.py` : intercepte les requêtes WSGI, détecte le host, réécrit le path vers `/<slug>/...` avant que Flask route
- Louis configure le CNAME manuellement dans Railway (Settings → Networking → Custom Domain) pour activer le HTTPS

### Auth admin
- Séparée de Flask-Login (session['admin_logged_in'])
- Credentials dans .env : ADMIN_EMAIL, ADMIN_PASSWORD

## Variables d'environnement

### Local (.env)
```
SECRET_KEY=
DATABASE_URL=sqlite:///vyranos.db
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
Ordre : `reservation` → `blocage` → `service` → `business` → `user`

## Déploiement Railway
- Service Flask + plugin PostgreSQL
- Gunicorn via `Procfile`, Python 3.12 via `.python-version`
- Chaque `git push` → redéploiement automatique
- Domaine custom : Settings → Networking → Custom Domain → `vyranos.app` (à faire quand domaine acheté)

## Lancer Claude Code
Toujours lancer depuis `/Users/louisblankaert/Desktop/vyranos/`.

## À faire
1. **Uploads prod** — logos/covers éphémères sur Railway → migrer vers Cloudinary ou S3
2. **Domaine `vyranos.app`** — acheter + configurer CNAME dans Railway
3. **Emails transactionnels (Resend)** — 3 emails à implémenter :
   - Notif à Louis quand un nouveau client s'inscrit
   - Confirmation de réservation au client final
   - Notification au commerçant quand il a un nouveau RDV

## Fait
- ✅ Pivot sur mesure — suppression templates DIY, abonnement Stripe, onboarding
- ✅ Domaines personnalisés — CNAME + WSGI middleware + page dashboard
- ✅ Admin — stats clients, suspendre/réactiver compte, gestion domaines
- ✅ Page publique unique (`public/landing.html`) avec `couleur_primaire` configurable
