from __future__ import print_function
import sys
import json
from os import environ
from base64 import b64encode
import requests
from six.moves.urllib.parse import urlencode
from nylas._client_sdk_version import __VERSION__
from nylas.client.util import url_concat
from nylas.client.restful_model_collection import RestfulModelCollection
from nylas.client.restful_models import (
    Calendar, Contact, Event, Message, Thread, File,
    Account, APIAccount, SingletonAccount, Folder,
    Label, Draft
)
from nylas.client.errors import (
    APIClientError, ConnectionError, NotAuthorizedError,
    InvalidRequestError, NotFoundError, MethodNotSupportedError,
    ServerError, ServiceUnavailableError, ConflictError,
    SendingQuotaExceededError, ServerTimeoutError, MessageRejectedError
)

DEBUG = environ.get('NYLAS_CLIENT_DEBUG')
API_SERVER = "https://api.nylas.com"


def _validate(response):
    status_code_to_exc = {400: InvalidRequestError,
                          401: NotAuthorizedError,
                          402: MessageRejectedError,
                          403: NotAuthorizedError,
                          404: NotFoundError,
                          405: MethodNotSupportedError,
                          409: ConflictError,
                          429: SendingQuotaExceededError,
                          500: ServerError,
                          503: ServiceUnavailableError,
                          504: ServerTimeoutError}
    request = response.request
    url = request.url
    status_code = response.status_code
    data = request.body

    if DEBUG:  # pragma: no cover
        print("{} {} ({}) => {}: {}".format(request.method, url, data,
                                            status_code, response.text))

    try:
        data = json.loads(data) if data else None
    except (ValueError, TypeError):
        pass

    if status_code == 200:
        return response
    elif status_code in status_code_to_exc:
        cls = status_code_to_exc[status_code]
        try:
            response = json.loads(response.text)
            kwargs = dict(url=url, status_code=status_code,
                          data=data)

            for key in ['message', 'server_error']:
                if key in response:
                    kwargs[key] = response[key]

            raise cls(**kwargs)

        except (ValueError, TypeError):
            raise cls(url=url, status_code=status_code,
                      data=data, message="Malformed")
    else:
        raise APIClientError(url=url, status_code=status_code,
                             data=data, message="Unknown status code.")


def nylas_excepted(func):
    def caught(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            server = args[0].api_server
            raise ConnectionError(url=server)
    return caught


class APIClient(json.JSONEncoder):
    """API client for the Nylas API."""

    def __init__(self, app_id=environ.get('NYLAS_APP_ID'),
                 app_secret=environ.get('NYLAS_APP_SECRET'),
                 access_token=environ.get('NYLAS_ACCESS_TOKEN'),
                 api_server=API_SERVER):
        if "://" not in api_server:
            raise Exception("When overriding the Nylas API server address, you"
                            " must include https://")
        self.api_server = api_server
        self.authorize_url = api_server + '/oauth/authorize'
        self.access_token_url = api_server + '/oauth/token'
        self.revoke_url = api_server + '/oauth/revoke'

        self.app_secret = app_secret
        self.app_id = app_id

        self.session = requests.Session()
        self.version = __VERSION__
        major, minor, revision, _, __ = sys.version_info
        version_header = 'Nylas Python SDK {} - {}.{}.{}'.format(self.version,
                                                                 major, minor,
                                                                 revision)
        self.session.headers = {'X-Nylas-API-Wrapper': 'python',
                                'User-Agent': version_header}
        self._access_token = None
        self.access_token = access_token
        self.auth_token = None

        # Requests to the /a/ namespace don't use an auth token but
        # the app_secret. Set up a specific session for this.
        self.admin_session = requests.Session()

        if app_secret is not None:
            b64_app_secret = b64encode((app_secret + ':').encode('utf8'))
            authorization = 'Basic {secret}'.format(
                secret=b64_app_secret.decode('utf8')
            )
            self.admin_session.headers = {
                'Authorization': authorization,
                'X-Nylas-API-Wrapper': 'python',
                'User-Agent': version_header,
            }
        super(APIClient, self).__init__()

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        if value:
            authorization = 'Bearer {token}'.format(token=value)
            self.session.headers['Authorization'] = authorization
        else:
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']

    def authentication_url(self, redirect_uri, login_hint=''):
        args = {'redirect_uri': redirect_uri,
                'client_id': self.app_id,
                'response_type': 'code',
                'scope': 'email',
                'login_hint': login_hint,
                'state': ''}

        return url_concat(self.authorize_url, args)

    def token_for_code(self, code):
        args = {'client_id': self.app_id,
                'client_secret': self.app_secret,
                'grant_type': 'authorization_code',
                'code': code}

        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}

        resp = requests.post(self.access_token_url, data=urlencode(args),
                             headers=headers).json()

        self.access_token = resp[u'access_token']
        return self.access_token

    def is_opensource_api(self):
        if self.app_id is None and self.app_secret is None:
            return True

        return False

    @nylas_excepted
    def revoke_token(self):
        resp = self.session.post(self.revoke_url)
        _validate(resp)
        self.auth_token = None
        self.access_token = None

    @property
    def account(self):
        return self._get_resource(SingletonAccount, '')

    @property
    def accounts(self):
        if self.is_opensource_api():
            return RestfulModelCollection(APIAccount, self)
        return RestfulModelCollection(Account, self)

    @property
    def threads(self):
        return RestfulModelCollection(Thread, self)

    @property
    def folders(self):
        return RestfulModelCollection(Folder, self)

    @property
    def labels(self):
        return RestfulModelCollection(Label, self)

    @property
    def messages(self):
        return RestfulModelCollection(Message, self)

    @property
    def files(self):
        return RestfulModelCollection(File, self)

    @property
    def drafts(self):
        return RestfulModelCollection(Draft, self)

    @property
    def contacts(self):
        return RestfulModelCollection(Contact, self)

    @property
    def events(self):
        return RestfulModelCollection(Event, self)

    @property
    def calendars(self):
        return RestfulModelCollection(Calendar, self)

    ##########################################################
    #   Private functions used by Restful Model Collection   #
    ##########################################################

    def _get_http_session(self, api_root):
        # Is this a request for a resource under the accounts/billing/admin
        # namespace (/a)? If the latter, pass the app_secret
        # instead of the secret_token
        if api_root == 'a':
            return self.admin_session
        return self.session

    @nylas_excepted
    def _get_resources(self, cls, extra=None, **filters):
        # FIXME @karim: remove this interim code when we've got rid
        # of the old accounts API.
        postfix = "/{}".format(extra) if extra else ''
        if cls.api_root != 'a':
            url = "{}/{}{}".format(
                self.api_server,
                cls.collection_name,
                postfix
            )
        else:
            url = "{}/a/{}/{}{}".format(
                self.api_server,
                self.app_id,
                cls.collection_name,
                postfix
            )

        url = url_concat(url, filters)
        response = self._get_http_session(cls.api_root).get(url)
        results = _validate(response).json()
        return [
            cls.create(self, **x)
            for x in results
            if x is not None
        ]

    @nylas_excepted
    def _get_resource_raw(self, cls, id, extra=None,
                          headers=None, **filters):
        """Get an individual REST resource"""
        headers = headers or {}
        headers.update(self.session.headers)

        postfix = "/{}".format(extra) if extra else ''
        if cls.api_root != 'a':
            url = "{}/{}/{}{}".format(self.api_server, cls.collection_name, id,
                                      postfix)
        else:
            url = "{}/a/{}/{}/{}{}".format(self.api_server, self.app_id,
                                           cls.collection_name, id, postfix)

        url = url_concat(url, filters)

        response = self._get_http_session(cls.api_root).get(url, headers=headers)
        return _validate(response)

    def _get_resource(self, cls, id, **filters):
        response = self._get_resource_raw(cls, id, **filters)
        result = response.json()
        if isinstance(result, list):
            result = result[0]
        return cls.create(self, **result)

    def _get_resource_data(self, cls, id,
                           extra=None, headers=None, **filters):
        response = self._get_resource_raw(cls, id, extra=extra,
                                          headers=headers, **filters)
        return response.content

    @nylas_excepted
    def _create_resource(self, cls, data, **kwargs):
        url = "{}/{}/".format(self.api_server, cls.collection_name)

        if kwargs:
            url = "{}?{}".format(url, urlencode(kwargs))

        session = self._get_http_session(cls.api_root)

        if cls == File:
            response = session.post(url, files=data)
        else:
            data = json.dumps(data)
            headers = {'Content-Type': 'application/json'}
            headers.update(self.session.headers)
            response = session.post(url, data=data, headers=headers)

        result = _validate(response).json()
        if cls.collection_name == 'send':
            return result
        return cls.create(self, **result)

    @nylas_excepted
    def _create_resources(self, cls, data):
        url = "{}/{}/".format(self.api_server, cls.collection_name)
        session = self._get_http_session(cls.api_root)

        if cls == File:
            response = session.post(url, files=data)
        else:
            data = json.dumps(data)
            headers = {'Content-Type': 'application/json'}
            headers.update(self.session.headers)
            response = session.post(url, data=data, headers=headers)

        results = _validate(response).json()
        return [cls.create(self, **x) for x in results]

    @nylas_excepted
    def _delete_resource(self, cls, id, data=None, **kwargs):
        name = cls.collection_name
        url = "{}/{}/{}".format(self.api_server, name, id)

        if kwargs:
            url = "{}?{}".format(url, urlencode(kwargs))
        session = self._get_http_session(cls.api_root)
        if data:
            _validate(session.delete(url, json=data))
        else:
            _validate(session.delete(url))

    @nylas_excepted
    def _update_resource(self, cls, id, data, **kwargs):
        name = cls.collection_name
        url = "{}/{}/{}".format(self.api_server, name, id)

        if kwargs:
            url = "{}?{}".format(url, urlencode(kwargs))

        session = self._get_http_session(cls.api_root)

        response = session.put(url, json=data)

        result = _validate(response).json()
        return cls.create(self, **result)

    @nylas_excepted
    def _call_resource_method(self, cls, id, method_name, data):
        """POST a dictionary to an API method,
        for example /a/.../accounts/id/upgrade"""
        name = cls.collection_name
        if cls.api_root != 'a':
            url = "{}/{}/{}/{}".format(self.api_server, name, id, method_name)
        else:
            # Management method.
            url = "{}/a/{}/{}/{}/{}".format(
                self.api_server,
                self.app_id,
                cls.collection_name,
                id,
                method_name,
            )

        session = self._get_http_session(cls.api_root)
        response = session.post(url, json=data)

        result = _validate(response).json()
        return cls.create(self, **result)
