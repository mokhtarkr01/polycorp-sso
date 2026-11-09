# Polycorp SSO: portal backed by a directory

SSO lab: OpenLDAP + Keycloak (IdP) + a SAML 2.0 portal (RH) + an OIDC portal (Notes).

## Structure
- `docker-compose.yml`: OpenLDAP and Keycloak containers
- `ldap/`: LDIF files (users, groups, service account, ACL)
- `portals/`: the two Flask apps (`rh_portal.py` SAML, `notes_portal.py` OIDC)
- `docs/`: the project report (PDF)

## Run
```bash
docker compose up -d
# load LDAP data
ldapadd -x -H ldap://localhost -D "cn=admin,dc=polycorp,dc=com" -w admin123 -f ldap/base.ldif
ldapadd -x -H ldap://localhost -D "cn=admin,dc=polycorp,dc=com" -w admin123 -f ldap/service.ldif
docker exec -i ldap ldapmodify -Y EXTERNAL -H ldapi:/// < ldap/acl.ldif
# portals
cd portals && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python rh_portal.py                                   # terminal 1, port 5000
NOTES_CLIENT_SECRET=<secret> python notes_portal.py   # terminal 2, port 5001
```
The Keycloak realm, LDAP federation, mappers and clients are configured in the
admin console (see the report in `docs/`).

## Warning
Laboratory project: the passwords in the files are lab values, there is no TLS,
and the servers run in development mode. Do not use as is in production.
