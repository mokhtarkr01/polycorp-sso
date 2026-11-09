import os
import json
from flask import Flask, redirect, session, url_for
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "notes-secret-change-me"
app.config["SESSION_COOKIE_NAME"] = "notes_session"

oauth = OAuth(app)
oauth.register(
    "keycloak",
    client_id="portal-notes",
    client_secret=os.environ["NOTES_CLIENT_SECRET"],
    server_metadata_url="http://localhost:8080/realms/polycorp/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email"},
)


def page(title, body):
    return f"<h1>{title}</h1>{body}<p><a href='/'>Home</a> | <a href='/logout'>Local logout</a></p>"


@app.route("/")
def index():
    return page("Portal Notes (OIDC)", "<p><a href='/notes'>Open my notes</a></p>")


@app.route("/login")
def login():
    return oauth.keycloak.authorize_redirect(url_for("callback", _external=True))


@app.route("/callback")
def callback():
    token = oauth.keycloak.authorize_access_token()
    session["user"] = dict(token["userinfo"])
    print("ID TOKEN:", token["id_token"], flush=True)
    with open("last_id_token.txt", "w") as f:
        f.write(token["id_token"])
    return redirect("/notes")


@app.route("/notes")
def notes():
    user = session.get("user")
    if not user:
        return redirect("/login")
    return page("My notes", f"<p>Welcome {user.get('preferred_username')}.</p><pre style='white-space:pre-wrap'>{json.dumps(user, indent=2)}</pre>")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
