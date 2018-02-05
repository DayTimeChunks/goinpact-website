
#  Console datastore
# http://localhost:8000/instances


# Get the Google database
from google.appengine.ext import db
# from google.appengine.ext import ndb

import os
import jinja2
from pybcrypt import bcrypt

template_dir = os.path.join(os.path.dirname(__file__), 'www')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True) # autoescape is important for security!!



# User stuff
def users_key(group = 'default'):
    return db.Key.from_path('users', group)

def make_pw_hash(email, pw, salt = None): # Course function
    if not salt:
        salt = bcrypt.gensalt()
    h = bcrypt.hashpw(email + pw, salt)
    return( "%s|%s" % (salt, h))

# def check_pw(name, pw, h):
#     salt = h.split("|")[2]
#     return h == hash_pw(name + pw, salt)

def valid_pw(email, pw, h): # Course function
    salt = h.split("|")[0]
    return h == make_pw_hash(email, pw, salt)

class User(db.Model):
    username = db.StringProperty(required = True)
    last_name = db.StringProperty(required = False)
    email = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = False)
    # If google user
    guser_id = db.StringProperty(required = False) # googleUser
    nickname = db.StringProperty(required = False) # googleUser

    avatar = db.BlobProperty() # For storing images
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    # @decorator:
    # means that you can call the
    # object's method without instantiating the object
    @classmethod
    def by_id(cls, uid):
        # 'cls' refers to the User class
        return cls.get_by_id(uid, parent = users_key())

    @classmethod
    def by_google_id(cls, gid):
        # 'cls' refers to the User class
        return cls.all().filter('guser_id =', gid).get()

    @classmethod
    def by_name(cls, username):
        # Query the db without GQL
        u = cls.all().filter('username =', username).get()
        return u

    @classmethod
    def by_email(cls, email):
        # Query the db without GQL
        u = cls.all().filter('email =', email).get()
        return u

    @classmethod
    def by_gtoken(cls, idtoken):
        # Query the db without GQL
        u = cls.all().filter('idtoken =', idtoken).get()
        return u

    @classmethod
    def register(cls, username, given_name, last_name, pw, email):
        pw_hash = make_pw_hash(email, pw)
        return User(parent = users_key(),
                    username = username,
                    given_name = given_name, # for google-signin
                    last_name = last_name,
                    pw_hash = pw_hash,
                    email = email)


    @classmethod
    def login(cls, email, password):
        u = cls.by_email(email)
        if u and valid_pw(email, password, u.pw_hash):
            return u

# Blog stuff
def blog_key(name='default'):
    # Method to organize the database in case more than one blog.
    return db.Key.from_path('blogs', name)

class Articles(db.Model):
    # create entities
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    image = db.BlobProperty() # For storing images
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    # Careful when naming properties, if
    # create a model, and get an error when using it first it will break that
    # propert and the name assigned (e.g. "location") won't work again.
    # My mistake was when I assigned
    # a['location'] = ...  instead of:
    # a.location = ...
    # location = db.GeoPtProperty()
    location2 = db.GeoPtProperty()
    coords = db.GeoPtProperty()
    map_url = db.StringProperty()

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        # Use global method render_str()
        return render_str("post.html", p = self) # self is 'art' (ie. one article)



    # TODO: define a similar method here for Articles.
    # @classmethod
    # def by_id(cls, id):
    #     # 'cls' refers to the User class
    #     return cls.get_by_id(id, parent = users_key())

# Exact same method as in the Handler class
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)
