import os
from flask import redirect, request
from flask_appbuilder.security.views import AuthOIDView
from flask_login import login_user
from flask_admin import expose
from urllib.parse import quote
import jwt
import logging

log = logging.getLogger(__name__)

# Set the OIDC field that should be used as a username
USERNAME_OIDC_FIELD = os.getenv('USERNAME_OIDC_FIELD', default='sub')
FIRST_NAME_OIDC_FIELD = os.getenv('FIRST_NAME_OIDC_FIELD',
                                  default='nickname')
LAST_NAME_OIDC_FIELD = os.getenv('LAST_NAME_OIDC_FIELD',
                                 default='name')


class AuthOIDCView(AuthOIDView):

    @expose('/login/', methods=['GET', 'POST'])
    def login(self, flag=True):
        sm = self.appbuilder.sm
        oidc = sm.oid

        @self.appbuilder.sm.oid.require_login
        def handle_login():
            log.debug(f"oidc.user_getfield('email') {oidc.user_getfield('email')}")
            # log.debug(f'request.args["next"], {request.args["next"]}')
            user = sm.auth_user_oid(oidc.user_getfield('email'))
            log.debug(f'user: {user}')
            if user is None:
                # info = oidc.user_getinfo([
                #     USERNAME_OIDC_FIELD,
                #     FIRST_NAME_OIDC_FIELD,
                #     LAST_NAME_OIDC_FIELD,
                #     'email',
                # ])
                log.debug('sm.add_user')
                email = oidc.user_getfield('email')
                try:
                    first_name = email.split('@')[0].split('.')[0]
                    last_name = email.split('@')[0].split('.')[1]
                except:
                    first_name = 'FirstName'
                    last_name = 'LastName'
                user = sm.add_user(
                    # username=info.get(USERNAME_OIDC_FIELD),
                    # first_name=info.get(FIRST_NAME_OIDC_FIELD),
                    # last_name=info.get(LAST_NAME_OIDC_FIELD),
                    # email=info.get('email'),
                    # role=sm.find_role(sm.auth_user_registration_role)

                    username=email,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    role=sm.find_role(sm.auth_user_registration_role)

                )

            login_user(user, remember=False)

            try:
                next_url = request.args["next"]
                if next_url == '' or next_url is None:
                    self.appbuilder.get_url_for_index
            except (KeyError, IndexError):
                next_url = self.appbuilder.get_url_for_index
            log.debug(f'next_url {next_url}')
            return redirect(next_url)

        return handle_login()

    @expose('/logout/', methods=['GET', 'POST'])
    def logout(self):

        oidc = self.appbuilder.sm.oid

        oidc.logout()
        super(AuthOIDCView, self).logout()
        redirect_url = request.url_root.strip(
            '/') + self.appbuilder.get_url_for_login

        logout_uri = oidc.client_secrets.get(
            'issuer') + '/protocol/openid-connect/logout?redirect_uri='
        if 'OIDC_LOGOUT_URI' in self.appbuilder.app.config:
            logout_uri = self.appbuilder.app.config['OIDC_LOGOUT_URI']

        return redirect(logout_uri + quote(redirect_url))
