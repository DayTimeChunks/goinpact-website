import os
import re
import jinja2
import webapp2
import urllib
import urllib2

from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import mail

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

# Authenticating users with google
from google.appengine.api import users

# Contact form messaging

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# To DEBUG the app.
import logging
logging.info('First logging INFO!')
logging.warning('First logging WARNING!')

template_dir = os.path.join(os.path.dirname(__file__), 'www')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               extensions=['jinja2.ext.autoescape'],
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
        template = jinja_env.get_template(template)
        return template.render(params) # parameters can also be a dictionary!
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
    def render_front(self):
        self.render("index.html")

    def get(self):
        self.render_front() # draw main page

    def post(self):
        have_error = False
        fname = self.request.get("fname")
        lname = self.request.get("lname")
        contact_subject = self.request.get("contact_subject")
        contact_email = self.request.get("contact_email")
        contact_message = self.request.get("contact_message")

        params = dict(fname = fname, lname = lname, c_email=contact_email,
                      c_subject=contact_subject, c_message=contact_message)

        if not fname:
            params['error_fname'] = "Please enter a first name"
            have_error = True
        if not lname:
            params['error_lname'] = "Please enter a last name"
            have_error = True
        if not valid_email(contact_email):
            params['error_email'] = "That's not a valid email"
            have_error = True
        if not contact_subject:
            params['error_subject'] = "Please add a subject"
            have_error = True
        if not contact_message:
            params['error_message'] = "Please add a message"
            have_error = True

        if have_error:
            self.render("index.html", **params)
        else:
            sender = "daytightchunks@gmail.com"
            to = "adappt@outlook.fr"
            cc = "inpact.messenger@gmail.com"

            full_name = fname + " " + lname
            msg = "Dear Antoine, " + full_name + " is trying to contact us. \n"
            msg += """ The message reads:

            """
            msg += contact_message
            msg += "\n\n The email address to respond to is: \n\n"
            msg += contact_email
            msg += "\n\n This is an automated message from our Contact Page! ;)"

            message = mail.EmailMessage()
            message.sender = sender
            message.to = [to, cc]
            message.subject = contact_subject
            message.body = msg
            # message.check_initialized()
            message.send()

        self.redirect("/contacted")


class Contacted(Handler):
    def get(self):
        self.render("contacted.html")


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

    def cookie_login(self, user):
        # self.set_secure_cookie('user_id', str(user.key().id())) # old db
        self.set_secure_cookie('user_id', str(user.key.integer_id())) # old db

    def cookie_logout(self):
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
        if self.user:
            u = User.by_id(int(uid))
            print("Initialize self.useremail:", u.email)


class BlogFront(Blog):
    # Open new page on "New post" button click
    def post(self):
        self.redirect("/blog/newpost")

    # Collect all articles in the database to render
    def get(self):
        # Query Method 1
        # arts = db.GqlQuery("SELECT * FROM Articles ORDER BY created DESC")
        # self.render("blog.html", arts=arts)
        # Query Method 2
        # arts = Articles.all().order('-created') # Old db
        arts = Articles.query().order(-Articles.created) # new ndb
        # Avoid querying the db again in jinja template!
        arts = list(arts) # Make a list of art objects
        if arts:
            self.render("blog.html", arts=arts)
            # self.render("blog.html", arts=new_art_list)
        else:
            self.render("blog.html")

class BlogFrontJson(Blog):
    # This handler converts each blog article into a
    # json readable object for computer parsing.
    def get(self):
        import json
        import datetime
        arts = Articles.query().order(-Articles.created)
        arts = list(arts)
        json_arts = []
        for a in arts:
            new_dict = {}
            new_dict['content'] = a.content
            new_dict['created'] = a.created.strftime("%a, %d %b %Y %H:%M:%S")
            # t = a.last_modified
            new_dict['last_modified'] = a.last_modified.strftime("%a, %d %b %Y %H:%M:%S")
            new_dict['subject'] = a.subject
            json_arts.append(new_dict)

        json_arts = json.dumps(json_arts)
        self.write(json_arts)

        # self.write()

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
            return ndb.GeoPt(lat, lon)

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
        image_lg = self.request.get("img_lg")
        image_md = self.request.get("img_md")
        image_sm = self.request.get("img_sm")
        lat = str(self.request.get("latitude")).strip()
        lon = str(self.request.get("longitude")).strip()

        # TODO:
        # Fix zoom level on maps, or make it dynamic!
        # loc = db.GeoPt(50.954873, 6.938495)
        # lat = 50.954873
        # lon = 6.938495


        if subject and content:
            a = Articles(subject=subject, content=content)
            a.author = self.user.username
            a.has_image = False
            # Another way with parent (course solution)
            # a = Articles(parent= blog_key(), subject=subject, content=content)

            if lat and lon:
                print("lat, lon:", lat, lon)

                # a.coords = db.GeoPt(lat, lon)
                a.map_url = gmaps_img([lat, lon])

            # Check and store uploaded images
            if image_lg:
                a.has_image = True
                a.image_lg = image_lg
            if image_md:
                a.has_image = True
                a.image_md = image_md
            if image_sm:
                a.has_image = True
                a.image_sm = image_sm

            a.put() # Saves the art object to the database
            # article_id = a.key().id() # old db
            article_id = a.key.integer_id() # new ndb
            # One way:
            # self.redirect("/blog/" + str(article_id), article_id)
            # Another way (solution):
            # Get will extract whatever is after '/blog/'
            # self.redirect("/blog/%s" % str(article_id))
            # TODO: Temporary redirect to a new location without jinja
            # 1. direct to permalink post
            # 2. on permalin khtml, include the link href= handler + ID
            # 3. on Thumnailer, leave as is...
            self.render('permalinktest.html', article_id = article_id)
            # self.redirect("/thumbnailer/%s" % str(article_id))
        else:
            error = "Please include both subject and content."
            self.render_post(subject=subject, content=content, error=error)

class ArticleView(Blog):
    # PostPage where Permalink.hmtml is run
    # article_id is passed from the webapp2 regex expression
    def get(self, article_id):
        # Parse article_id, checking if ends in .json
        # If json, return a json object, othersie find the article
        parsed = article_id.split(".")
        if len(parsed) == 1:
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

            self.render("permalinkpost.html", article=article)
        else:
            import json
            import datetime
            article = Articles.get_by_id(int(parsed[0]))
            json_art = [{"content": article.content,
                         "created": article.created.strftime("%a, %d %b %Y %H:%M:%S"),
                         "last_modified": article.last_modified.strftime("%a, %d %b %Y %H:%M:%S"),
                         "subject": article.subject}]
            json_art = json.dumps(json_art)
            self.write(json_art)

# TODO:
# Enable multiple images....
# This class renders the image once in the html
class Thumbnailer(Blog):
    def get(self, article_id):
        article = Articles.get_by_id(int(article_id))
        thumbnail = None
        if article:
            img_lg = images.Image(article.image_lg)
            if img_lg:
                img_lg.resize(width=400, height=265)
                thumbnail = img_lg.execute_transforms(output_encoding=images.JPEG)
                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(thumbnail)
            else:
                return
        else:
            return
        # self.render("permalinktest.html", thumbnail = thumbnail)


# class ImgServe(webapp2.Requesthandler):
#     def get(self, resource):
#         pass



# TODO: Changed from PermTest
class EmailTest(Blog):
    def get(self):
        sender = "daytightchunks@gmail.com"
        to = "pablo.alv.zal@gmail.com"
        # mail.send_mail(sender=sender,
        #                to=to,
        #                subject="Your subject test",
        #                body="This is your message"
        #                )
        # self.render("permalinktest.html")

        message = mail.EmailMessage()
        message.sender = sender
        message.to = [to, sender]
        message.subject = 'a subject'
        message.body = 'This is an email to you'
        # message.check_initialized()
        message.send()
        self.redirect("/")

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
        g_url = users.create_login_url('/login') # Will redirect back here to get() if g_url button is used.
        g_url_txt = 'Sign up with Google'
        self.render("signup.html", g_url=g_url, g_url_txt=g_url_txt)

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
            self.cookie_login(u) # Used for new users and old users
            self.redirect("/welcome")

class Login(Blog):
    def get(self):
        # If user chooses Google Sign-in
        user = users.get_current_user() # Returns email address
        if user:
            nickname = user.nickname()
            guser_id = user.user_id() # This is unique, email address may change.
            email = user.email()
            logging.warning("guser_id: %s" % guser_id)
            logging.warning("email: %s" % user.email())
            logging.warning("user: %s" % user)

            # Check if google user exists in database:
            u = User.by_google_id(guser_id)
            old_user = User.by_email(email)

            # Old inPact user, now using Google Signin for the first time
            if old_user and not u:
                old_user.user_id = user_id
                old_user.nickname = nickname
                old_user.email = email
                old_user.put()
                self.cookie_login(u)
            # Both google details and old user exists
            elif u and old_user:
                msg = 'User already exists'
                logging.warning(msg)
                self.cookie_login(u)
            else:
                u = User(parent = users_key(),
                         guser_id = guser_id,
                         email = email,
                         username = nickname,
                         nickname = nickname)
                u.put()
                self.cookie_login(u) # Used for new users and old users

            logging.warning('user True, get_current_user(): %s' % user)
            self.redirect("/welcome")

        else:
            g_url = users.create_login_url(self.request.uri) # Will redirect back here to get() if g_url button is used.
            g_url_txt = 'Login with Google'
            self.render("login.html", g_url=g_url, g_url_txt=g_url_txt)


    def post(self):
        email = self.request.get("email")
        password = self.request.get("password")

        # Check is user registered via our form
        u = User.login(email, password)
        if u:
            self.cookie_login(u)
            self.redirect("/welcome")
        else:
            msg = "Invalid email and password"
            self.render("login.html", error_username = msg)

class Logout(Blog):
    # reset user_id cookie to nothing
    # check if user signed in with Google
    def get(self):
        user = users.get_current_user()
        if user: # Google user?
            self.cookie_logout()
            self.redirect(users.create_logout_url("/"))
            # self.write(repr(users.get_current_user() ) )
        else:
            self.cookie_logout()
            self.redirect("/")

class Welcome(Blog):
    # This will be "my inPact" page..
    def get(self):
        if self.user:
            self.render('welcome.html',
                        username = self.user.username)
        else:
            self.redirect('/login')

# To see the local datastore:
# localhost:8000/datastore
class Debug(Blog):
    def get(self):
        users = User.query().order('-username')
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
        ndb.put_multi(to_put)
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
                               ('/contacted', Contacted),
                               ('/support', Support),
                               ('/team', Team),
                               ('/blog/?', BlogFront), # See note below on "?"
                               ('/blog/.json', BlogFrontJson),
                               ('/blog/(\d+)|[json]', ArticleView),
                               ('/thumbnailer/(\d+)', Thumbnailer),
                               ('/blog/newpost', NewPost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
                               ('/debug', Debug) # ,
                               # ('/permalinktest/(\d+)', PermTest) #, ('/update_schema', UpdateSchemaHandler)
                              ],
                              debug = True)  # CHange to False during production
# The debug=True parameter tells webapp2 to print stack traces to the browser output if a handler encounters an error or raises an uncaught exception. This option should be removed before deploying the final version of your application, otherwise you will inadvertently expose the internals of your application.

# BlogFront Handler
# "?" means handler will match if the slash at the end is there or not. It is a way for the handler not to care if a slash is included or not. Equivalent to : '/blog'

# Regex Notes:
# \d is a digit (a character in the range 0-9), and + means 1 or more times. So, \d+ is 1 or more digits.
# \w alphanumeric [a-zA-Z0-9_]
# \S matches any non-whitespace character; this is equivalent to the set [^ \t\n\r\f\v]

# https://docs.python.org/2/library/re.html

# On URL encoding:
# If you use such URL-safe keys, don't use sensitive data such as email addresses as entity identifiers. A possible solution would be to use a hash of the sensitive data as the identifier.
#  From:  https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entities
