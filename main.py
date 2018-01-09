import os
import re
import jinja2
import webapp2
# import bcrypt
from pybcrypt import bcrypt
# from libs.bcrypt import bcrypt
# import cgi

template_dir = os.path.join(os.path.dirname(__file__), 'www')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True) # autoescape is important for security!!

# Get the Google database
from google.appengine.ext import db
# from google.appengine.ext import ndb

def hash_str(s, salt = None):
    if not salt:
        salt = bcrypt.gensalt()
    h = bcrypt.hashpw(s, salt)
    return( "%s|%s|%s" % (s, h, salt))

def check_str(s, h):
    salt = h.split('|')[1]
    if h == hash_str(s, salt):
        return s

secret = str('movethissecrettoanewmodule')
def make_secure_val(val, secret, salt = None):
    if not salt:
        salt = bcrypt.gensalt()
    h = bcrypt.hashpw(val + secret, salt)
    return( '%s|%s|%s' % (val, h, salt))


def check_secure_val(secure_value):
    cookie_val = secure_value.split("|")[0]
    salt = secure_value.split("|")[2]
    if secure_value == make_secure_val(cookie_val, secret, salt):
        return cookie_val

# def check_secure_withsalt(triple_str):
#     salt = triple_str.split('|')[2]
#     val = triple_str.split("|")[0]
#     if triple_str == hash_str(val, salt):
#         return val

# def hash_pw(name, pw, salt = None):
#     if not salt:
#         salt = bcrypt.gensalt()
#     h = bcrypt.hashpw(name + pw, salt)
#     return( "%s|%s|%s" % (name, h, salt))

def make_pw_hash(name, pw, salt = None): # Course function
    if not salt:
        salt = bcrypt.gensalt()
    h = bcrypt.hashpw(name + pw, salt)
    return( "%s|%s" % (salt, h))

# def check_pw(name, pw, h):
#     salt = h.split("|")[2]
#     return h == hash_pw(name + pw, salt)

def valid_pw(name, pw, h): # Course function
    salt = h.split("|")[0]
    return h == make_pw_hash(name, pw, salt)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
    def render_front(self):
        self.render("index.html")

    def get(self):
        self.render_front() # draw main page

class Support(Handler):
    def get(self):
        self.render("support.html")

class Team(Handler):
    def get(self):
        self.render("team.html")


# Blog stuff
def blog_key(name='default'):
    # Method to organize the database in case more than one blog.
    return db.Key.from_path('blogs', name)

class Blog(Handler):

    def set_secure_cookie(self, name, value):
        cookie_val = make_secure_val(value, secret) # 3x string
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s; Path=/' % (name, cookie_val))
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        # Return cookie_val if both are True
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        # app engine has a function that gets called every request
        # Here we check to see if user is logged in or not (on every request)
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        print("secure uid:", uid)
        # Keep track of every user
        self.user = uid and User.by_id(int(uid))
        print("Initialize self.user:", self.user)


class BlogFront(Blog):

    # Open new page on "New post" button click
    def post(self):
        self.redirect("/blog/newpost")

    # Collect all articles in the database to render (moed from Blog handler)
    def get(self):
        # Query Method 1
        # arts = db.GqlQuery("SELECT * FROM Articles ORDER BY created DESC")
        # self.render("blog.html", arts=arts)
        # Query Method 2
        posts = Articles.all().order('-created')
        self.render("blog.html", arts=posts)

    # def get(self):
    #     # Handle user cookies:
    #     userid_str = self.request.cookies.get('user_id')
    #     if userid_str:
    #         name = userid_str.split("|")[0]
    #
    #     # Track user visits
    #     visits = 0
    #
    #     cookie_val = read_secure_cookie('visits')
    #     if cookie_val:
    #         visits = int(cookie_val)
    #     visits += 1
    #
    #     # Update cookie
    #     set_secure_cookie('visits', visits)
    #
    #     # Older code to do the above
    #     # salt = None
    #     # visit_cookie_str = self.request.cookies.get('visits')
    #     # Separate value and hash, check hash
    #     # if visit_cookie_str:
    #     #     salt = visit_cookie_str.split("|")[2]
    #     #     cookie_val = check_secure_withsalt(visit_cookie_str)
    #     #     if cookie_val:
    #     #         visits = int(cookie_val)
    #     # new_cookie_val = hash_str(str(visits), salt)
    #     # self.response.headers.add_header('Set-Cookie', 'visits=%s' % str(new_cookie_val))
    #
    #     self.render_blog()

class NewPost(Blog):
    # redirected from New Post click button on BlogFront
    def get(self):
        if self.user:
            # print("self.user:", self.user.name)
            self.render_post()
        else:
            self.redirect('/login')

    def render_post(self, subject="", content="", error=""):
        self.render("newpost.html", subject=subject, content=content, error=error)

    def post(self):
        # Get new post data
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            a = Articles(subject=subject, content=content)
            # Another way with parent (course solution)
            # a = Articles(parent= blog_key(), subject=subject, content=content)

            a.put() # Saves the art object to the database
            article_id = a.key().id()
            # One way:
            # self.redirect("/blog/" + str(article_id), article_id)
            # Another way (solution):
            # Get will extract whatever is after '/blog/'
            self.redirect("/blog/%s" % str(article_id))
        else:
            error = "Please include both subject and content."
            self.render_post(subject=subject, content=content, error=error)

# Sign-up required functions
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)
    # the above is equivalent to return truish if 2nd arg is true, else return 1st arg
PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)
    # Return object, else False if email is empty or none if no match

class SignUp(Blog):
    # TODO
    #  Read about memcash for dealing with two simultaneous
    #  registrations with the same user name.
    #  Memcash will handle the database registration via atomic operations

    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        self.username = self.request.get("username")
        self.last_name = self.request.get("last_name")
        self.email = self.request.get("email")
        self.password = self.request.get("password")
        self.verify = self.request.get("verify")

        params = dict(username = self.username, last_name = self.last_name,
                      email = self.email)
        if not valid_username(self.username):
            params['error_username'] = "That's not a valid user name"
            have_error = True
        if not valid_username(self.last_name):
            params['error_last_name'] = "That's not a valid last name"
            have_error = True
        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email"
            have_error = True
        if not valid_password(self.password):
            params['error_password'] = "That's not a valid password"
            have_error = True
        if self.password != self.verify:
            params['error_verify'] = "Your passwords did not match"
            have_error = True

        if have_error:
            self.render("signup.html", **params)
        else:
            self.done() # implements Register.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Register(SignUp):
    def done(self):
        u = User.by_email(self.email)
        if u:
            msg = 'User already exists'
            # params['error_user_exists'] = msg
            self.render("signup.html", error_username = msg)
        else:
            u = User.register(self.username, self.last_name, self.password, self.email)
            u.put()

            self.login(u) # Used for new users and old users
            self.redirect("/welcome")

class Login(Blog):
    def get(self):
        self.render("login.html")

    def post(self):
        email = self.request.get("email")
        # self.email = self.request.get("email")
        password = self.request.get("password")

        u = User.login(email, password)
        if u:
            self.login(u)
            self.redirect("/welcome")
        else:
            msg = "Invalid email and password"
            self.render("login.html", error_username = msg)

class Logout(Blog):
    # reset user_id cookie to nothing
    def get(self):
        self.logout()
        # self.redirect("/login")
        self.redirect("/blog")



class Welcome(Blog):
    # TODO
    # This will be "my inPact" page..
    def get(self):
        # Check if user id (uid) exists
        # We have access to it because of the Handler class inheritance
        print("self.user: ", self.user)
        if self.user:
            self.render('welcome.html', username = self.user.username)
        else:
            self.redirect('/login')

        # Handle user cookies:
        # userid_str = self.request.cookies.get('user_id')
        # if userid_str:
        #     name = userid_str.split("|")[0]
        # else:
        #     name = "Not logged id"
        # self.response.out.write("Welcome, %s" % name)

class ArticleView(Blog):
    # PostPage where Permalink.hmtml is run
    # article_id is passed from the webapp2 regex expression
    def get(self, article_id):
        # One way
        article = Articles.get_by_id(int(article_id))
        #  Another way (solution)
        # key = db.Key.from_path('Post', int(article_id), parent=blog_key())
        # post = db.get(Key)

        # In case of user hack
        if not article:
            self.error(404)
            # Include your own 404 html response
            return

        # subject = article.subject
        # content = article.content
        # self.render("mypost.html", subject=subject, content=content)
        self.render("permalinkpost.html", article=article)

# User stuff
def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    username = db.StringProperty(required = True)
    last_name = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)

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
    def register(cls, username, last_name, pw, email):
        pw_hash = make_pw_hash(username, pw)
        return User(parent = users_key(),
                    username = username,
                    last_name = last_name,
                    pw_hash = pw_hash,
                    email = email)

    # TODO: not sure if by_email method is working
    @classmethod
    def login(cls, email, password):
        u = cls.by_email(email)
        if u and valid_pw(email, password, u.pw_hash):
            return u


class Debug(Blog):
    def get(self):
        users = User.all().order('-username')
        if users:
            print("Users", users)
            self.render("debug.html", users = users)
        else:
            self.write("No users")

    def post(self):
        usr_key = self.request.get("delete-user")
        user_to_delete = User.get(usr_key)
        user_to_delete.delete()
        # print("usr to delete: ", user_to_delete)
        self.redirect('/debug')


class Articles(db.Model):
    # create entities
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    avatar = db.BlobProperty() # For storing images
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        # Use global method render_str()
        return render_str("post.html", p = self)

# Exact same method as in the Handler class
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/support', Support),
                               ('/team', Team),
                               ('/blog/?', BlogFront),
                               ('/blog/(\d+)', ArticleView),
                               ('/blog/newpost', NewPost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
                               ('/debug', Debug)
                              ],
                              debug = True)

# Regex Notes:
# \d is a digit (a character in the range 0-9), and + means 1 or more times. So, \d+ is 1 or more digits.

# On URL encoding:
# If you use such URL-safe keys, don't use sensitive data such as email addresses as entity identifiers. A possible solution would be to use a hash of the sensitive data as the identifier.
#  From:  https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entities
