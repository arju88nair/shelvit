from .db import db
import datetime
from flask_bcrypt import generate_password_hash, check_password_hash
from mongoengine.errors import FieldDoesNotExist, DoesNotExist
from util.errors import TokenNotFound, InternalServerError
from util.slugGenerator import generateSlug


class Board(db.Document):
    title = db.StringField(required=True)
    symbol = db.StringField()
    description = db.StringField(default="A board to hold everything and anything related to you")
    is_admin = db.BooleanField(default=False)
    slug = db.StringField()
    color = db.StringField()
    added_by = db.ReferenceField('User')
    created_at = db.DateTimeField()
    modified_at = db.DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.modified_at = datetime.datetime.now()
        self.slug = generateSlug()
        return super(Board, self).save(*args, **kwargs)


class Item(db.Document):
    title = db.StringField()
    source = db.StringField(required=True)
    # source_url = db.URLField(required=True)
    source_url = db.URLField()
    summary = db.StringField()
    item_type = db.StringField(required=True)
    content = db.StringField()
    slug = db.StringField()
    board = db.ReferenceField('Board', required=True)
    keywords = db.ListField()
    tags = db.ListField()
    added_by = db.ReferenceField('User')
    created_at = db.DateTimeField()
    modified_at = db.DateTimeField(default=datetime.datetime.now)
    liked_by = db.ListField()
    like_count = db.IntField()

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.modified_at = datetime.datetime.now()
        return super(Item, self).save(*args, **kwargs)


class User(db.Document):
    username = db.StringField(required=True, unique=True)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True, min_length=6)
    imageURL = db.StringField()
    verified = db.BooleanField(default=False)
    is_active = db.BooleanField(default=True)
    items = db.ListField(db.ReferenceField('Item', reverse_delete_rule=db.PULL))
    board = db.ListField(db.ReferenceField('Board', reverse_delete_rule=db.PULL))
    created_at = db.DateTimeField()
    modified_at = db.DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.modified_at = datetime.datetime.now()
        return super(User, self).save(*args, **kwargs)

    def hash_password(self):
        self.password = generate_password_hash(self.password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


User.register_delete_rule(Item, 'added_by', db.CASCADE)
User.register_delete_rule(Board, 'added_by', db.PULL)


class RevokedTokenModel(db.Document):
    jti = db.StringField()
    token_type = db.StringField(null=False)
    user_identity = db.StringField(null=False)
    revoked = db.BooleanField(null=False)
    expires = db.DateTimeField()
    created_at = db.DateTimeField(default=datetime.datetime.now)
    modified_at = db.DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.now()
        self.modified_at = datetime.datetime.now()
        return super(RevokedTokenModel, self).save(*args, **kwargs)

    @classmethod
    def is_jti_blacklisted(cls, jti):
        try:
            query = RevokedTokenModel.objects.get(jti=jti)
            return query.revoked
        except(DoesNotExist, FieldDoesNotExist):
            raise TokenNotFound
        except Exception:
            raise InternalServerError


class Comment(db.Document):
    item_id = db.ReferenceField('Item')
    slug = db.StringField()
    full_slug = db.StringField()
    comment = db.StringField()
    created_at = db.DateTimeField(default=datetime.datetime.now)
    modified_at = db.DateTimeField(default=datetime.datetime.now)
    added_by = db.ReferenceField('User')
    liked_by = db.ListField()
    like_count = db.IntField()


class Like(db.EmbeddedDocumentListField):
    user_id = db.ReferenceField('User')
    created_at = db.DateTimeField(default=datetime.datetime.now)
    modified_at = db.DateTimeField(default=datetime.datetime.now)


class AuthMethods(db.Document):
    name = db.StringField()


class AuthProvider(db.Document):
    provider_key = db.StringField()
    added_by = db.ReferenceField('User')
    method_id = db.ReferenceField('AuthMethod')
