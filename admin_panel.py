from flask import Flask, redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models import Client, AutoReplyRule, MessageLog, Base
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# Flask app
flask_app = Flask(__name__)
flask_app.secret_key = os.getenv("SECRET_KEY")

# Database
engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(sessionmaker(bind=engine))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Admin User (separate from Client) ──────────────────────────────
class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

login_manager = LoginManager(flask_app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser("admin")
    return None


# ── Secure Base View ───────────────────────────────────────────────
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("login"))


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        
        # Stats for dashboard
        total_clients = db_session.query(Client).count()
        total_messages = db_session.query(MessageLog).count()
        total_rules = db_session.query(AutoReplyRule).count()
        active_clients = db_session.query(Client).filter(Client.is_active == True).count()
        
        return self.render(
            "admin/index.html",
            total_clients=total_clients,
            total_messages=total_messages,
            total_rules=total_rules,
            active_clients=active_clients
        )


# ── Custom Views ───────────────────────────────────────────────────
class ClientView(SecureModelView):
    column_list = ["id", "business_name", "email", "whatsapp_number", "is_active", "created_at"]
    column_searchable_list = ["business_name", "email"]
    column_filters = ["is_active"]
    form_excluded_columns = ["hashed_password", "rules", "messages", "created_at"]
    can_export = True

    # Hash password on create
    def on_model_change(self, form, model, is_created):
        if is_created and hasattr(form, "password") and form.password.data:
            model.hashed_password = pwd_context.hash(form.password.data)


class RuleView(SecureModelView):
    column_list = ["id", "client_id", "trigger_keyword", "response_text", "is_active", "created_at"]
    column_searchable_list = ["trigger_keyword"]
    column_filters = ["is_active", "client_id"]
    can_export = True


class MessageLogView(SecureModelView):
    column_list = ["id", "client_id", "sender_number", "message_text", "direction", "timestamp"]
    column_filters = ["direction", "client_id"]
    column_searchable_list = ["sender_number", "message_text"]
    can_create = False
    can_edit = False
    can_delete = False
    can_export = True


# ── Admin Setup ────────────────────────────────────────────────────
admin = Admin(
    flask_app,
    name="WhatsApp Automation Admin",
    index_view=SecureAdminIndexView()
)

admin.add_view(ClientView(Client, db_session, name="Clients"))
admin.add_view(RuleView(AutoReplyRule, db_session, name="Auto-Reply Rules"))
admin.add_view(MessageLogView(MessageLog, db_session, name="Message Logs"))


# ── Login / Logout Routes ──────────────────────────────────────────
@flask_app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            login_user(AdminUser("admin"))
            return redirect(url_for("admin.index"))
        error = "Invalid credentials"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: #f8f9fa; }}
            .login-card {{ max-width: 400px; margin: 100px auto; }}
        </style>
    </head>
    <body>
        <div class="login-card card shadow p-4">
            <h3 class="text-center mb-4">WhatsApp Admin</h3>
            {"<div class='alert alert-danger'>" + error + "</div>" if error else ""}
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-success w-100">Login</button>
            </form>
        </div>
    </body>
    </html>
    """


@flask_app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    flask_app.run(port=5000, debug=True)