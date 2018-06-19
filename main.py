import os
import re
import jinja2
import webapp2
import urllib
import urllib2
import datetime # json-page writes.
import time # for timestamps (checking memcache writes)

from google.appengine.api import memcache
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
from maps import *

# keys
from my_keys import *

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


# For memecache:
DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development')

# CLIENT_ID = "<enter-own-client-id-here>.apps.googleusercontent.com"

def hash_str(s, salt = None):
    if not salt:
        salt = bcrypt.gensalt()
    h = bcrypt.hashpw(s, salt)
    return( "%s|%s|%s" % (s, h, salt))

def check_str(s, h):
    salt = h.split('|')[1]
    if h == hash_str(s, salt):
        return s


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

    # Email function (Contatc Page)
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

class Project(Handler):
    def get(self):
        self.render("project.html")


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
        self.set_secure_cookie('user_id', str(user.key.integer_id()))

    def cookie_admin(self, user):
        self.set_secure_cookie('admin_id', str(user.key.integer_id()))

    def cookie_logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def cookie_admin_out(self):
        self.response.headers.add_header('Set-Cookie', 'admin_id=; Path=/')

    def initialize(self, *a, **kw):
        # app engine has a function that gets called every request
        # Here we check to see if user is logged in or not (on every request)
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        # print("secure uid:", uid)
        # Keep track of every user
        self.user = uid and User.by_id(int(uid))
        # print("Initialize self.user:", self.user)
        # if self.user:
        #     u = User.by_id(int(uid))
            # print("Initialize self.useremail:", u.email)

# Initialize counter value, used in bump_counter()
memcache.set(key="counter", value=0)
time_at_cache = time.time()
def top_arts(update = False):
    # Store article list in a memcache object
    key = 'top' # Will be the reference to the value we will store here.
    logging.warning("Getting CACHE")
    logging.warning("Update valu was: %s" % update)
    arts = memcache.get(key, for_cas=True)
    # print("arts from cache: ", arts)
    if arts is None or update: # Query the database
        logging.warning("Running a DB Query == Moneyyyy!")
        bump_counter(key)
        arts = memcache.get(key)
        # print("arts from query: ", arts)
    return arts

def bump_counter(key):
   client = memcache.Client()
   max_retries = 99
   n = 0
   while True:
       n += 1
       if max_retries == n:
           print("Reached max retires")
           break # Aoid infinite loop
       counter = client.gets('counter')
       if counter is None:
           memcache.set(key="counter", value=0)
           counter = client.gets('counter')
           if counter is None:
               raise KeyError('Uninitialized counter')
       if client.cas('counter', counter+1):
           arts = Articles.query().order(-Articles.created)
           arts = list(arts) # Avoids querying the db again in jinja template!
           r = memcache.set(key, arts) # True or False
           if r:
               time_at_cache = time.time()
           else:
               logging.debug("Memecache failed to reset!!!")
           # print("Is success? memcache.set(key, arts): ", r)
           # print("client.gets('counter'): ", client.gets('counter'))
           break
       else:
           time.sleep(min(64, (2 ** n)) + (random.randint(0, 1000) / 1000))

class BlogFront(Blog):
    # Collect all articles in the database to render
    def get(self):
        arts = top_arts()
        if arts:
            time_now = time.time()
            time_since = time_now - time_at_cache
            self.render("blog.html", arts=arts)
            self.write("queried " + str(round(time_since, 2)))

            # self.render("blog.html", arts=new_art_list)
        else:
            self.render("blog.html")

    # Open new page on "New post" button click
    def post(self):
        self.redirect("/blog/newpost")

class BlogFrontJson(Blog):
    # This handler converts each blog article into a
    # json readable object for computer parsing.
    def get(self):
        import json
        # arts = Articles.query().order(-Articles.created)
        arts = top_arts()
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

class NewPost(Blog):
    # redirected from New Post click button on BlogFront
    def get(self):
        if self.user:
            user = users.get_current_user()
            if user and users.is_current_user_admin():
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
        image_1st = self.request.get("img_1st")
        image_1st_w = self.request.get("img_1st_w")
        image_1st_h = self.request.get("img_1st_h")

        image_2nd = self.request.get("img_2nd")
        image_2nd_w = self.request.get("img_2nd_w")
        image_2nd_h = self.request.get("img_2nd_h")
        image_3rd = self.request.get("img_3rd")
        image_3rd_w = self.request.get("img_3rd_w")
        image_3rd_h = self.request.get("img_3rd_h")
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
                # print("lat, lon:", lat, lon)
                # a.coords = db.GeoPt(lat, lon)
                a.map_url = gmaps_img([lat, lon])

            # Check and store uploaded images
            images_num = 0
            if image_1st:
                a.image_1st = image_1st
                a.image_1st_w = image_1st_w if str(image_1st_w) else str(1200)
                a.image_1st_h = image_1st_h if str(image_1st_h) else str(750)
                images_num += 1
            if image_2nd:
                a.image_2nd = image_2nd
                a.image_2nd_w = image_2nd_w if str(image_2nd_w) else str(200)
                a.image_2nd_h = image_2nd_h if str(image_2nd_h) else str(200)
                images_num += 1
            if image_3rd:
                a.image_3rd = image_3rd
                a.image_3rd_w = image_3rd_w if str(image_3rd_w) else str(500)
                a.image_3rd_h = image_3rd_h if str(image_3rd_h) else str(300)
                images_num += 1

            a.has_image = True if images_num > 0 else False
            a.images_num = images_num
            a.put() # Saves the art object to the database
            # article_id = a.key().id() # old db
            article_id = a.key.integer_id() # new ndb
            # Needed to move the memcache update to ArticleView,
            # because memcache and database were not sinking.
            # Maybe to do with sending a request?
            self.redirect("/storeme/%s" % str(article_id))
        else:
            error = "Please include both subject and content."
            self.render_post(subject=subject, content=content, error=error)

class StoreArticle(Blog):
    def get(self, article_id):
        # Updating the CACHE
        # CACHE.clear() # Empty the cache to update on next query risks a chache stampede!
        logging.warning("Wrting New Post")
        logging.warning("Calling top_arts(True)")
        narts = top_arts(update = True) # Query the ndb only on new writes.
        logging.warning("New arts length: %s" % len(narts))
        self.redirect("/blog/%s" % str(article_id))



class ArticleView(Blog):
    # PostPage where Permalink.hmtml is run
    # article_id is passed from the webapp2 regex expression
    def get(self, article_id):
        # logging.warning("URL: %s" % str(self.request.url))
        # Parse article_id, checking if ends in .json
        # If json, return a json object, othersie find the article
        parsed = article_id.split(".")
        if len(parsed) == 1:
            # TODO: use memcache instead!
            # store the article in memcash, with its key as id,
            # when someone views the same article, it will be in the cache.
            # will need to use the .add(key, article) function if not found on existing.
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

    def post(self):
        article_id = self.request.get("edit-post")
        self.redirect("/editpost/%s" % str(article_id))

class EditPost(Blog):
    def get(self, article_id):
        article_to_edit = Articles.get_by_id(int(article_id))
        if article_to_edit:
            self.render("editpost.html", article=article_to_edit)
        else:
            self.error(404)
            # Include your own 404 html response
            return

    def render_post(self, subject="", content="", error=""):
        # Debug to see if coordinates work:
        # This will write my machine's ip
        # self.write(self.request.remote_addr)
        # Debug the whole thing
        # "repr" is a way to avoid' pythons "<...>" response, which would otherwise be read as a html "tag" and thus be able to post the response to the page
        # self.write(repr(get_coords(self.request.remote_addr)))
        self.render("editpost.html", subject=subject, content=content, error=error)

    def post(self, article_id):
        article = Articles.get_by_id(int(article_id))
        # logging.warning("URL: %s" % str(self.request.url))
        # logging.warning("article_id: %s" % str(article_id))
        subject = self.request.get("subject")
        content = self.request.get("content")

        image_1st_delete = self.request.get("img-1st-delete")
        image_2nd_delete = self.request.get("img-2nd-delete")
        image_3rd_delete = self.request.get("img-3rd-delete")

        image_1st = self.request.get("img_1st")
        image_1st_w = self.request.get("img_1st_w")
        image_1st_h = self.request.get("img_1st_h")

        logging.warning("image with user selected? %s" % image_1st_w)

        if not image_1st_w and image_1st:
            image_1st_w = str(article.image_1st_w)
        if not image_1st_h and image_1st:
            image_1st_h = str(article.image_1st_h)

        logging.warning("image with old obj selected? %s" % image_1st_w)

        image_2nd = self.request.get("img_2nd")
        image_2nd_w = self.request.get("img_2nd_w")
        image_2nd_h = self.request.get("img_2nd_h")
        if not image_2nd_w and image_2nd:
            image_2nd_w = str(article.image_2nd_w)
        if not image_2nd_h and image_2nd:
            image_2nd_h = str(article.image_2nd_h)

        image_3rd = self.request.get("img_3rd")
        image_3rd_w = self.request.get("img_3rd_w")
        image_3rd_h = self.request.get("img_3rd_h")
        if not image_3rd_w and image_3rd:
            image_3rd_w = str(article.image_3rd_w)
        if not image_3rd_h and image_3rd:
            image_3rd_h = str(article.image_3rd_h)

        delete_1st = delete_2nd = delete_3rd = False
        if image_1st_delete and not image_1st:
            delete_1st = True
        if image_2nd_delete and not image_2nd:
            delete_2nd = True
        if image_3rd_delete and not image_3rd:
            delete_3rd = True

        map_delete = True if self.request.get("map-delete") else False
        lat = str(self.request.get("latitude")).strip()
        lon = str(self.request.get("longitude")).strip()

        #  Update article
        if subject and content:
            article.subject = subject
            article.content = content

            # Store/delete images
            images_num = article.images_num # 0 to 3
            has_image = article.has_image # True or False
            if image_1st:
                had_1st_img = True if article.image_1st else False
                article.image_1st = None
                article.image_1st = image_1st
                article.image_1st_w = image_1st_w if str(image_1st_w) else str(1200)
                article.image_1st_h = image_1st_h if str(image_1st_h) else str(750)
                if not had_1st_img:
                    images_num += 1
            elif delete_1st:
                article.image_1st = None
                images_num -= 1

            if image_2nd:
                had_2nd_img = True if article.image_2nd else False
                article.image_2nd = None
                article.image_2nd = image_2nd
                article.image_2nd_w = image_2nd_w if str(image_2nd_w) else str(200)
                article.image_2nd_h = image_2nd_h if str(image_2nd_h) else str(200)
                if not had_2nd_img:
                    images_num += 1
            elif delete_2nd:
                article.image_2nd = None
                images_num -= 1

            if image_3rd:
                had_3rd_image = True if article.image_3rd else False
                article.image_3rd = None
                article.image_3rd = image_3rd
                article.image_3rd_w = image_3rd_w if str(image_3rd_w) else str(500)
                article.image_3rd_h = image_3rd_h if str(image_3rd_h) else str(300)
                if not had_3rd_image:
                    images_num += 1
            elif delete_3rd:
                article.image_3rd = None
                images_num -= 1

            article.has_image = True if images_num > 0 else False
            article.images_num = images_num

            if lat and lon:
                map_delete = False
                # a.coords = db.GeoPt(lat, lon)
                article.map_url = gmaps_img([lat, lon])

            article.put()
            self.redirect("/storeme/%s" % str(article_id))
            # self.redirect("/blog/%s" % str(article_id))
        else:
            error = "Please include both subject and content."
            # TODO: not sure if second argument will work...???
            # self.redirect("/editpost/%s" % str(article_id), error=error)
            self.render_post(subject=subject, content=content, error=error)
            # TODO, see how NewPost is written..., L:318



# This class renders the image in the html <img> element
# It works for BlogFront and articles with 1 picture only
class Thumbnailer(Blog):
    def get(self, article_id):
        article = Articles.get_by_id(int(article_id))
        thumbnail = None
        if article:
            img_1st = images.Image(article.image_1st)
            w = int(article.image_1st_w)
            h = int(article.image_1st_h)
            if img_1st and int(w) and int(h):
                img_1st.resize(width=w, height=h)
                thumbnail = img_1st.execute_transforms(output_encoding=images.JPEG)
                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(thumbnail)
            else:
                return
        else:
            return

# Not the most efficient solution, as
# for the article with three images, the database will be
# queried 6 times for the same entity (3 on render + 3 on JS manipulation).
class OtherPic(Blog):
    def get(self, article_id, pic_num):
        article = Articles.get_by_id(int(article_id))
        print("pic_num: ", pic_num)
        thumbnail = None
        if article:
            if pic_num == 'image_3rd':
                img = images.Image(article.image_3rd)
                w = int(article.image_3rd_w)
                h = int(article.image_3rd_h)
            else:
                img = images.Image(article.image_2nd)
                w = int(article.image_2nd_w)
                h = int(article.image_2nd_h)
            if img and int(w) and int(h):
                img.resize(width=w, height=h)
                image = img.execute_transforms(output_encoding=images.JPEG)
                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(image)
            else:
                return
        else:
            return

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
            u = User.register(self.username, self.last_name, self.password, self.email)
            u.put()
            self.cookie_login(u) # Used for new users and old users
            self.redirect("/welcome")

class Login(Blog):
    def get(self):
        # If user chooses Google Sign-in
        # if not, the "post()" method below will be followed.
        isAdmin = False
        user = users.get_current_user() # Returns email address
        if user:
            if (users.is_current_user_admin()):
                isAdmin = True

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
                old_user.user_id = guser_id
                old_user.nickname = nickname
                old_user.email = email
                old_user.put()
                self.cookie_login(old_user)
                if (isAdmin):
                    self.cookie_admin(old_user)
            # Both google details and old user exists
            elif u and old_user:
                msg = 'User already exists'
                logging.warning(msg)
                self.cookie_login(u)
                if (isAdmin):
                    self.cookie_admin(u)
            else:
                u = User(parent = users_key(),
                         guser_id = guser_id,
                         email = email,
                         username = nickname,
                         nickname = nickname)
                u.put()
                self.cookie_login(u) # Used for new users and old users
                if (isAdmin):
                    self.cookie_admin(u)

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
            msg = "Invalid email and/or password"
            self.render("login.html", error_username = msg, email=email)

class Logout(Blog):
    # reset user_id cookie to nothing
    # check if user signed in with Google
    def get(self):
        user = users.get_current_user()
        if user: # Google user?
            self.cookie_logout()
            self.cookie_admin_out()
            self.redirect(users.create_logout_url("/"))
            # self.write(repr(users.get_current_user() ) )
        else:
            self.cookie_admin_out()
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
        # user_to_delete = User.get(usr_key) # Old db
        user_to_delete = usr_key.get() # New ndb
        user_to_delete.delete()
        # print("usr to delete: ", user_to_delete)
        self.redirect('/debug')


# Not yet used, to be used when needing to re-design the db structure
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
                               ('/storeme/(\d+)', StoreArticle),
                               ('/editpost/(\d+)', EditPost),
                               ('/thumbnailer/(\d+)', Thumbnailer),
                               ('/otherpic/(\d+)/(\w+)', OtherPic), # Need to optimize how these are generated.
                               ('/blog/newpost', NewPost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/project', Project),
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
