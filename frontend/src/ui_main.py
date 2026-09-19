from nicegui import app, ui
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("BACKEND_URL")+ os.getenv("API_V1_STR")

# Helper pour ajouter automatiquement le token JWT aux requêtes
def get_auth_headers():
    token = app.storage.user.get("access_token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@ui.page("/")
def login_page():
  # Variable d'état pour basculer entre Connexion et Inscription
  if app.storage.user.get("authenticated", False):
    ui.navigate.to("/dashboard")
    return

  is_registering = False

  with ui.card().classes("absolute-center p-8 w-96 shadow-lg rounded-lg"):
    title_label = ui.label("Connexion - Fitness App").classes(
        "text-h5 font-bold mb-4 text-center"
    )

    username_input = ui.input("Nom d'utilisateur").classes("w-full mb-2")
    password_input = ui.input("Mot de passe", password=True).classes(
        "w-full mb-4"
    )

    def handle_submit():
        endpoint = "/auth/register" if is_registering else "/auth/login"
        data = {
            "username": username_input.value,
            "password": password_input.value,
        }

        try:
            response = requests.post(f"{API_URL}{endpoint}", json=data)
            if response.status_code == 200:
                res_data = response.json()
                if is_registering:
                    app.storage.user["authenticated"] = True
                    app.storage.user["username"] = username_input.value
                    ui.notify(
                        "Inscription réussie ! Vous pouvez vous connecter.",
                        type="positive",
                    )
                    
                    ui.navigate.to("/first-step")
                else:
                    # Succès de la connexion : on stocke la session
                    app.storage.user["authenticated"] = True
                    app.storage.user["username"] = username_input.value
                    app.storage.user["access_token"] = res_data.get("access_token")
                    ui.notify("Connexion réussie !", type="positive")
                    # Ici, on pourra rediriger vers le tableau de bord des workouts
                    if res_data.get("has_profile", False):
                        ui.navigate.to("/dashboard")  # Déjà fait -> Dashboard
                    else:
                        ui.navigate.to("/first-step")
            else:
                error_msg = response.json().get("detail", "Erreur inconnue")
                ui.notify(error_msg, type="negative")
        except Exception as e:
            ui.notify(f"Impossible de joindre le serveur : {e}", type="negative")

    submit_btn = ui.button(
        "Se connecter", on_click=handle_submit
    ).classes("w-full bg-primary text-white mb-2")

    toggle_btn = ui.button(
        "Créer un compte",
        on_click=lambda: toggle_mode(),
    ).classes("w-full bg-gray-200 text-gray-700")

    def toggle_mode():
      nonlocal is_registering
      is_registering = not is_registering
      if is_registering:
        title_label.text = "Inscription - Fitness App"
        submit_btn.text = "S'inscrire"
        toggle_btn.text = "Déjà un compte ? Se connecter"
      else:
        title_label.text = "Connexion - Fitness App"
        submit_btn.text = "Se connecter"
        toggle_btn.text = "Créer un compte"


@ui.page("/first-step")
def first_step_page():
    # if app.storage.user.get("authenticated", False):
    #     ui.navigate.to("/first-step")
    #     return
    if not app.storage.user.get("authenticated", False):
        ui.navigate.to("/")
        return

    username = app.storage.user.get("username")

    try:
        res = requests.get(f"{API_URL}/profile/check/{username}", headers=get_auth_headers())
        if res.status_code == 200 and res.json().get("has_profile", False):
        # Le profil existe déjà ! On bloque l'accès et on renvoie au dashboard
            ui.notify("Vous avez déjà configuré votre profil.", type="warning")
            ui.navigate.to("/dashboard")
            return
    except Exception as e:
        ui.notify(
            f"Impossible de vérifier le profil auprès du serveur : {e}",
            type="negative",
        )
    with ui.card().classes("absolute-center p-6 w-96 shadow-lg rounded-lg"):
        ui.label("Mon Profil & Objectifs").classes("text-h6 font-bold mb-4")

        age_input = ui.number("Âge", value=25).classes("w-full mb-2")
        gender_select = ui.select(
            ["Homme", "Femme", "Autre"], label="Sexe", value="Homme"
        ).classes("w-full mb-2")
        height_input = ui.number(
            "Taille (cm)", value=175, format="%.1f"
        ).classes("w-full mb-2")
        current_w_input = ui.number(
            "Poids actuel (kg)", value=70.0, format="%.1f"
        ).classes("w-full mb-2")
        target_w_input = ui.number(
            "Poids cible (kg)", value=68.0, format="%.1f"
        ).classes("w-full mb-4")

        def submit_profile():
            endpoint = "/profile/"
            payload = {
                "username": username,
                "age": int(age_input.value),
                "gender": gender_select.value,
                "height": float(height_input.value),
                "current_weight": float(current_w_input.value),
                "target_weight": float(target_w_input.value),
            }

            try:
                response = requests.post(f"{API_URL}{endpoint}", json=payload, headers=get_auth_headers())
                if response.status_code == 200:
                    ui.notify("Profil mis à jour avec succès !", type="positive")
                    ui.navigate.to("/dashboard")
                else:
                    ui.notify("Erreur lors de la sauvegarde", type="negative")
            except Exception as e:
                ui.notify(f"Erreur de connexion : {e}", type="negative")

        ui.button("Enregistrer", on_click=submit_profile).classes(
            "w-full bg-primary text-white"
        )
    
    
    
    # with ui.card().classes("absolute-center p-8 w-96 shadow-lg rounded-lg"):
    #     ui.label("Bienvenue !").classes("text-h5 font-bold mb-4 text-center")
    #     ui.label(
    #         "Vous êtes maintenant connecté. Commencez par ajouter vos premiers workouts !"
    #     ).classes("mb-4 text-center")
    #     ui.button(
    #         "Aller au tableau de bord",
    #         on_click=lambda: ui.navigate.to("/dashboard"),
    #     ).classes("w-full bg-primary text-white")

@ui.page("/profile")
def profile_page():
    if not app.storage.user.get("authenticated", False):
        ui.navigate.to("/")
        return

    username = app.storage.user.get("username")
    # Conteneur principal du formulaire
    with ui.card().classes("absolute-center p-6 w-96 shadow-lg rounded-lg"):
        ui.label("Paramètres du Profil").classes("text-h6 font-bold mb-4")

        # Champs du formulaire (initialisés à vide ou par défaut)
        age_input = ui.number("Âge").classes("w-full mb-2")
        gender_select = ui.select(
            ["Homme", "Femme", "Autre"], label="Sexe"
        ).classes("w-full mb-2")
        height_input = ui.number("Taille (cm)", format="%.1f").classes(
            "w-full mb-2"
        )
        current_w_input = ui.number("Poids actuel (kg)", format="%.1f").classes(
            "w-full mb-2"
        )
        target_w_input = ui.number("Poids cible (kg)", format="%.1f").classes(
            "w-full mb-4"
        )
        
        try:
            response = requests.get(f"{API_URL}/profile/{username}", headers=get_auth_headers())
            if response.status_code == 200:
                data = response.json()
                age_input.value = data.get("age")
                gender_select.value = data.get("gender")
                height_input.value = data.get("height")
                current_w_input.value = data.get("current_weight")
                target_w_input.value = data.get("target_weight")
        except Exception as e:
            ui.notify(
            f"Impossible de charger les données du profil : {e}", type="negative"
        )
        def update_profile():
            payload = {
                "username": username,
                "age": int(age_input.value or 0),
                "gender": gender_select.value,
                "height": float(height_input.value or 0),
                "current_weight": float(current_w_input.value or 0),
                "target_weight": float(target_w_input.value or 0),
            }

            try:
                res = requests.post(f"{API_URL}/profile/", json=payload, headers=get_auth_headers())
                if res.status_code == 200:
                    ui.notify("Profil mis à jour avec succès !", type="positive")
                else:
                    ui.notify("Erreur lors de la mise à jour", type="negative")
            except Exception as e:
                ui.notify(f"Erreur de connexion : {e}", type="negative")
        ui.button("Enregistrer les modifications", on_click=update_profile).classes(
            "w-full bg-primary text-white mb-2"
        )
        ui.button(
            "Retour au Dashboard", on_click=lambda: ui.navigate.to("/dashboard")
        ).props("flat").classes("w-full")
  

@ui.page("/dashboard")
def dashboard_page():
    if not app.storage.user.get("authenticated", False):
        ui.navigate.to("/")
        return

    username = app.storage.user.get("username", "Utilisateur")
    
    def logout():
            app.storage.user.clear()  # Efface la session
            ui.navigate.to("/")
    
    with ui.row().classes(
      "w-full items-center justify-between bg-primary text-white p-4 shadow-md"):
        # 1. Logo ou Titre (visible partout)
        ui.label(f"💪 Fitness App").classes("text-h6 font-bold")

        # 2. VERSION PC : Liens affichés directement (Caché sur mobile grâce à 'hidden md:flex')
        # with ui.row().classes("hidden md:flex lg:flex items-center gap-6"):
        #     ui.link("Dashboard", "/dashboard").classes("text-white no-underline")
        #     ui.link("Mes Séances", "/workouts").classes("text-white no-underline")
        #     ui.button("Déconnexion", on_click=logout).props("flat color=white")
        #     ui.label(f"Bienvenue, {username} !").classes("text-h6 font-bold")
        # 3. VERSION MOBILE : Menu Hamburger (Visible uniquement sur mobile grâce à 'md:hidden')
        with ui.row().classes():
            with ui.button(icon="menu").props("flat color=white"):
                with ui.menu():
                    with ui.menu_item(on_click=lambda: ui.navigate.to("/dashboard")):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("dashboard") 
                            ui.label("Dashboard")
                    ui.separator()
                    ui.menu_item("Mes Séances", lambda: ui.navigate.to("/workouts"))
                    ui.separator()
                    with ui.menu_item(on_click=lambda: ui.navigate.to("/chatbot")):
                        with ui.row().classes("items-center"):
                            ui.icon("smart_toy")
                            ui.label("Agents IA")
                    ui.separator()
                    ui.menu_item(f"Connecté en tant que {username}", lambda: None).props("disable")
                    with ui.menu_item(on_click=lambda: ui.navigate.to("/profile")):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("person")  # ou "account_circle"
                            ui.label("Mon Profil")
                    ui.separator()
                    with ui.menu_item(on_click=logout):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("logout")
                            ui.label("Déconnexion")
        
            
    with ui.card().classes("absolute-center p-8 w-96 shadow-lg rounded-lg"):
        ui.label("Bienvenue sur le tableau de bord des workouts !").classes(
        "text-h5 font-bold mb-4 text-center"
    )
    # Ici, vous pouvez ajouter des composants pour afficher les workouts, ajouter de nouveaux workouts, etc.
    

ui.run(port=8001, title="Fitness App", favicon="💪", storage_secret=os.getenv("STORAGE_SECRET"))