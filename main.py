import os
import jinja2
import webapp2


# TODO: Blog needs to refresh after new post submission!


template_dir = os.path.join(os.path.dirname(__file__), 'www')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True) # autoescape is important for security!!

# Get the Google database
from google.appengine.ext import db
# from google.appengine.ext import ndb

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
    # Collect all articles in the database to render
    def render_blog(self):
        # arts = ndb.GqlQuery("SELECT * FROM Articles ORDER BY created DESC")
        arts = db.GqlQuery("SELECT * FROM Articles ORDER BY created DESC")
        self.render("blog.html", arts=arts)

    def get(self):
        self.render_blog()
    # Open new page on "New post" button click
    def post(self):
        self.redirect("/blog/newpost")

class NewPost(Handler):
    def render_post(self, subject="", content="", error=""):
        self.render("newpost.html", subject=subject, content=content, error=error)

    # def get(self, article=""):
    #     article = article
    #     if article:
    #         subject = article.subject
    #         content = article.content
    #         self.render_post(subject=subject, content=content)
    #     else:
    #         self.render_post()

    def get(self):
        self.render_post()

    def post(self):
        # Get new post data
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            a = Articles(subject=subject, content=content)
            a.put() # Saves the art object to the database
            article_id = a.key().id()
            self.redirect("/blog/" + str(article_id), article_id)
        else:
            error = "Please include both subject and content."
            self.render_post(subject=subject, content=content, error=error)

class ArticleView(Handler):
    def get(self, article_id):
        article = Articles.get_by_id(int(article_id))
        # article_key = db.Key(article_url)
        # article = article_key.get()
        subject = article.subject
        content = article.content
        self.render("mypost.html", subject=subject, content=content)

    # def post(self):
    #     # Handle the edit button, to go back to your article to edit.
    #     # self.redirect("/blog/newpost", article=article)
    #     self.redirect("/blog/newpost")


class Articles(db.Model):
    # create entities
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    avatar = db.BlobProperty()
    created = db.DateTimeProperty(auto_now_add = True)



app = webapp2.WSGIApplication([('/', MainPage),
                               ('/support', Support),
                               ('/team', Team),
                               ('/blog', Blog),
                               ('/blog/newpost', NewPost),
                               ('/blog/(\d+)', ArticleView)
                              ],
                              debug = True)

# Regex Notes:
# \d is a digit (a character in the range 0-9), and + means 1 or more times. So, \d+ is 1 or more digits.

# On URL encoding:
# If you use such URL-safe keys, don't use sensitive data such as email addresses as entity identifiers. A possible solution would be to use a hash of the sensitive data as the identifier.
#  From:  https://cloud.google.com/appengine/docs/standard/python/ndb/creating-entities
