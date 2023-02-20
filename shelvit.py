import datetime
from flask import Flask
from database.db import initialize_db
import flask.scaffold

flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api
from util.errors import errors
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, get_jwt, create_access_token, get_jwt_identity, set_access_cookies
from util.routes import initialize_routes
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)

# //TODO Fix security issues
api = Api(app, errors=errors)


# Using an `after_request` callback, we refresh any token that is within 30
# minutes of expiring. Change the timedeltas to match the needs of your application.
@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.datetime.now(datetime.timezone.utc)
        target_timestamp = datetime.datetime.timestamp(now + datetime.timedelta())
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response


bcrypt = Bcrypt(app)
jwt = JWTManager(app)
app.config.from_pyfile('env.py')

# app.config["JWT_COOKIE_SECURE"] = False
# app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(False)  # Need to change in Prod

app.config['JWT_SECRET_KEY'] = app.config.get("JWT_SECRET_KEY")
app.config['MONGODB_SETTINGS'] = app.config.get("MONGODB_SETTINGS")
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://localhost/til'
}
app.config['CORS_HEADERS'] = 'Content-Type'

initialize_db(app)
initialize_routes(api)
if __name__ == "__main__":
    app.run(debug=True)
    app.run(host='0.0.0.0')
    app.run(port=5000)
