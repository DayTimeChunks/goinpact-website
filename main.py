import os
import re
import jinja2
import webapp2
import urllib
import urllib2

from google.appengine.api import images

from xml.dom import minidom

# Problems importing this library on production:
# from google.oauth2 import id_token
# from google.auth.transport import requests
# import six
# from six.moves import http_client
# import bcrypt
from pybcrypt import bcrypt
# from libs.bcrypt import bcrypt
# import cgi

# Data Models
import models_v1
from models_v1 import *

template_dir = os.path.join(os.path.dirname(__file__), 'www')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True) # autoescape is important for security!!



CLIENT_ID = "902461304999-hgej779q0upelr8ejpoeqfj5k0tppm2k.apps.googleusercontent.com"

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


class Blog(Handler):

    def set_secure_cookie(self, name, value):
        cookie_val = make_secure_val(value, secret) # 3x string
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s; Path=/' % (name, cookie_val))
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        # Return cookie_val if both are True
        return cookie_val and check_secure_val(cookie_val)

    def read_google_cookie(self):
        # Name should be 'idtoken'
        return self.request.cookies.get('idtoken')

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
        arts = Articles.all().order('-created')
        # Avoid querying the database twice!
        # i.e. Once here and once by jinja template



        arts = list(arts)
        if arts:
            for art in arts:
                print(art.key())

        # print("posts length:", len(posts))
        if arts:
            self.render("blog.html", arts=arts)
            # self.write(repr(arts))
            # print(len(arts))
        else:
            self.write(repr(arts))
            print(arts)

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

# Use this for the course.
# Later, allow user to provide the coordinates
# directly through the user-interface and post the map
def get_coords(ip):
    # API that loads the address based on the ip address provided
    ip = '4.2.2.2' # Deguggin hardcoded ip
    url = 'http://api.hostip.info/?ip=' + str(ip)
    content = None

    try:
        request = urllib2.Request(url)
        # Identify yourself! Be polite, say Hi!
        request.add_header('User-Agent', 'TheinPactProject/1.0 +http://diveintopython.org/  daytightchunks@gmail.com')
        opener = urllib2.build_opener()

        # content = urllib2.urlopen(url).read()
        content = opener.open(request).read()
    except urllib2.URLError, e:
        print e.fp.read()
        return

    if content:
        # parse the xml and find the coordinates
        xml = minidom.parseString(content)
        coords = xml.getElementsByTagName('gml:coordinates')[0].lastChild.nodeValue
        if coords:
            lon, lat = coords.split(',')
            # print(lat, lon)
            return db.GeoPt(lat, lon)

def gmaps_img(points):
    # points is a list of tuples, [[lat, lon], [lat, lon]]
    GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
    # Add the string 'markers=lat,lon' for each element in points and separate with '&'
    # markers = '&'.join('markers=%s,%s' % (p[0], p[1]) for p in points)  # For when a long list of markes is given
    # FOr only one coordinate pair.
    markers = 'markers=%s,%s' % (points[0], points[1])
    return GMAPS_URL + markers

def get_token(self):
    url = 'http://localhost:8080/tokensignin'
    content = None
    try:
        request = urllib2.Request(url)
        # Identify yourself! Be polite, say Hi!
        request.add_header('User-Agent', 'TheinPactProject/1.0 +http://goinpact.org/  daytightchunks@gmail.com')
        opener = urllib2.build_opener()

        # content = urllib2.urlopen(url).read()
        content = opener.open(request).read()
    except urllib2.URLError, e:
        self.write(e.fp.read())
        return

    if content:
        self.write(repr(content.headers.items()))
    else:
        self.write("No token found")

class NewPost(Blog):
    # redirected from New Post click button on BlogFront
    def get(self):
        if self.user:
            # print("self.user:", self.user.name)
            self.render_post()
        else:
            self.redirect('/login')

    def render_post(self, subject="", content="", error=""):

        # Debug to see if coordinates work:
        # This will write my machine's ip
        # self.write(self.request.remote_addr)
        # Debug the whole thing
        # "repr" is a way to avoid' pythons "<...>" response, which would otherwise be read as a html "tag" and thus be able to post the response to the page
        # self.write(repr(get_coords(self.request.remote_addr)))
        self.render("newpost.html", subject=subject, content=content, error=error)

    def post(self):
        # Get new post data
        subject = self.request.get("subject")
        content = self.request.get("content")
        img = self.request.get("img")
        lat = str(self.request.get("latitude")).strip()
        lon = str(self.request.get("longitude")).strip()

        # TODO:
        # Fix zoom level on maps, or make it dynamic!


        # loc = db.GeoPt(50.954873, 6.938495)
        # lat = 50.954873
        # lon = 6.938495


        if subject and content:
            a = Articles(subject=subject, content=content)
            # Another way with parent (course solution)
            # a = Articles(parent= blog_key(), subject=subject, content=content)

            if lat and lon:
                print("lat, lon:", lat, lon)

                # a.coords = db.GeoPt(lat, lon)
                a.map_url = gmaps_img([lat, lon])

            # a.location2 = loc
            if img:
                img = images.resize(img, 400, 300)
                a.image = img

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

class PermTest(Blog):
    def get(self):
        self.render("permalinktest.html")

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
        self.given_name = self.request.get("given_name")
        self.last_name = self.request.get("last_name")
        self.email = self.request.get("email")
        self.password = self.request.get("password")
        self.verify = self.request.get("verify")

        params = dict(username = self.username, last_name = self.last_name, email = self.email)
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
            u = User.register(self.username, self.given_name, self.last_name, self.password, self.email)
            u.put()
            self.login(u) # Used for new users and old users
            self.redirect("/welcome")

class Login(Blog):
    def get(self):
        idtoken = self.read_google_cookie()
        if (idtoken):
            print('Google idtoken on /login get():', idtoken)
            self.redirect("/glogin")

        # API course section...
        # p = urllib2.urlopen('https://goinpact0.appspot.com/login')
        # p = urllib2.urlopen('https://www.example.com')
        # c = p.read()
        # print(p.headers.items())
        # print('Directory')
        # print(dir(p))
        # print('Header items')
        # print(p.headers.items())
        #
        # print('Search by Key on headers')
        # print(p.headers['content-type'])
        # print(p.headers['server'])

        # p = urllib2.urlopen('http://www.nytimes.com/services/xml/rss/nyt/GlobalHome.xml')
        # c = p.read()
        # x = minidom.parseString(c)
        # print('Dir')
        # # print(dir(x))
        # print('Elements')
        # print(x.getElementsByTagName('item').length)

        self.render("login.html")

    def post(self):
        email = self.request.get("email")
        # self.email = self.request.get("email")
        password = self.request.get("password")

        # Check is user registered via our form
        u = User.login(email, password)

        # Check is user registered vai google sign-in
        # 1) Check that the id_token provided by google matches an id_token of an exisiting user

        if u:
            self.login(u)
            self.redirect("/welcome")
        else:
            msg = "Invalid email and password"
            self.render("login.html", error_username = msg)

class Glogin(Blog):
    def get(self):
        # get_token(self)
        # ####
        # Check is user registered vai google sign-in
        # 1) Check that the id_token provided by google matches an id_token of an exisiting user
        # token = self.read_google_cookie()
        # print('Google idtoken:', token)
        # self.render('welcome.html')

        # ####
        # API approach to getting header information

        # p = urllib2.urlopen('https://goinpact0.appspot.com/glogin')
        # c = p.read()
        # print(p.headers.items())

        # url = 'http://www.google.com/humans.txt'
        url = 'http://localhost:8080/tokensignin'
        try:
            result = urllib2.urlopen(url)
            print(result.headers.items())
            # self.response.out.write(result.read())
            self.response.out.write(result.headers.items())

        except urllib2.URLError, e:
            self.write(e.fp.read())
            # logging.exception('Caught exception fetching url')



        # ####
        # Once we have a validated token...

        # u_google = User.login_google(idtoken)
        # u_google.put()
        # if u_google:
        #     self.login(u_google) # Sets secure cookie for user id (own, not google's)
        #     self.redirect("/welcome")
        # else:
        #     msg = "Invalid email and password"
        #     self.render("login.html", error_username = msg)


        # ... if not, create a new user with googleUser info
        #  ... if yes, get User from database via idtoken

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


# To see the local datastore:
# localhost:8000/datastore
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



class UpdateSchemaHandler(webapp2.RequestHandler):
    """Queues a task to start updating the model schema."""
    def post(self):
        deferred.defer(update_schema_task)
        self.response.write("""
        Schema update started. Check the console for task progress.
        <a href="/">View entities</a>.
        """)

def update_schema_task(cursor=None, num_updated=0, batch_size=100):
    """Task that handles updating the models' schema.

    This is started by
    UpdateSchemaHandler. It scans every entity in the datastore for the
    Picture model and re-saves it so that it has the new schema fields.
    """

    # Force ndb to use v2 of the model by re-loading it.
    reload(models_v1) # this is where the model classes live

    # Get all of the entities for this Model.
    # query = models_v1.Picture.query()
    query = models_v1.Articles.query()
    articles, next_cursor, more = query.fetch_page(
        batch_size, start_cursor=cursor)

    to_put = []
    for art in articles:
        # Give the new fields default values.
        # If you added new fields and were okay with the default values, you
        # would not need to do this.
        return
        # art.location2 = db.GeoPt(50.138007, 8.698043)
        # # picture.avg_rating = 5
        # to_put.append(art)

    # Save the updated entities.
    if to_put:
        # ndb.put_multi(to_put)
        db.put_multi(to_put)
        num_updated += len(to_put)
        logging.info(
            'Put {} entities to Datastore for a total of {}'.format(
                len(to_put), num_updated))

    # If there are more entities, re-queue this task for the next page.
    if more:
        deferred.defer(
            update_schema_task, cursor=next_cursor, num_updated=num_updated)
    else:
        logging.debug(
            'update_schema_task complete with {0} updates!'.format(
                num_updated))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/support', Support),
                               ('/team', Team),
                               ('/blog/?', BlogFront),
                               ('/blog/(\d+)', ArticleView),
                               ('/blog/newpost', NewPost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/glogin', Glogin),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
                               ('/debug', Debug),
                               ('/permalinktest', PermTest) #, ('/update_schema', UpdateSchemaHandler)
                              ],
                              debug = True)  # CHange to False during production
# The debug=True parameter tells webapp2 to print stack traces to the browser output if a handler encounters an error or raises an uncaught exception. This option should be removed before deploying the final version of your application, otherwise you will inadvertently expose the internals of your application.



# Regex Notes:
# \d is a digit (a character in the range 0-9), and + means 1 or more times. So, \d+ is 1 or more digits.

# On URL encoding:
# If you use such URL-safe keys, don't use sensitive data such as email addresses as entity identifiers. A possible solution would be to use a hash of the sensitive data as the identifier.
#  From:  https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entities
