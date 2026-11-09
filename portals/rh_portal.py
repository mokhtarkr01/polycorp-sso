import base64
from flask import Flask, request, redirect, session
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

app = Flask(__name__)
app.secret_key = "rh-secret-change-me"
app.config["SESSION_COOKIE_NAME"] = "rh_session"

IDP_METADATA = "http://localhost:8080/realms/polycorp/protocol/saml/descriptor"
idp = OneLogin_Saml2_IdPMetadataParser.parse_remote(IDP_METADATA)

SETTINGS = {
    "strict": True,
    "debug": True,
    "sp": {
        "entityId": "http://localhost:5000/saml/metadata",
        "assertionConsumerService": {
            "url": "http://localhost:5000/saml/acs",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
    },
    "idp": idp["idp"],
    "security": {"requestedAuthnContext": False},
}


def init_auth():
    req = {
        "https": "off",
        "http_host": request.host,
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
    }
    return OneLogin_Saml2_Auth(req, SETTINGS)


def page(title, body):
    return f"<h1>{title}</h1>{body}<p><a href='/'>Home</a> | <a href='/logout'>Local logout</a></p>"


@app.route("/")
def index():
    return page("Portal RH (SAML)", "<p><a href='/rh'>Open the RH space</a></p>")


@app.route("/login")
def login():
    return redirect(init_auth().login())


@app.route("/saml/acs", methods=["POST"])
def acs():
    raw = base64.b64decode(request.form["SAMLResponse"]).decode("utf-8", errors="replace")
    with open("raw_response.xml", "w") as f:
        f.write(raw)
    auth = init_auth()
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        return f"SAML error: {errors} - {auth.get_last_error_reason()}", 400
    session["user"] = {"name_id": auth.get_nameid(), "attributes": auth.get_attributes()}
    with open("last_assertion.xml", "w") as f:
        f.write(auth.get_last_response_xml())
    return redirect("/rh")


@app.route("/rh")
def rh():
    user = session.get("user")
    if not user:
        return redirect("/login")
    attrs = user["attributes"]
    roles = attrs.get("roles", []) or attrs.get("Role", [])
    if "rh" not in roles:
        return page("403 - Access denied",
                    f"<p>{user['name_id']} is authenticated but is not in group rh.</p><p>Roles: {roles}</p>"), 403
    return page("RH space", f"<p>Welcome {user['name_id']}.</p><pre>{attrs}</pre>")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
