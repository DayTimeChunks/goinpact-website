
# From the Handler

class BlogFront(Blog):
    # Removed this from the current handler definition
    def get(self):
        # Handle user cookies:
        userid_str = self.request.cookies.get('user_id')
        if userid_str:
            name = userid_str.split("|")[0]

        # Track user visits
        visits = 0

        cookie_val = read_secure_cookie('visits')
        if cookie_val:
            visits = int(cookie_val)
        visits += 1

        # Update cookie
        set_secure_cookie('visits', visits)

        # Older code to do the above
        # salt = None
        # visit_cookie_str = self.request.cookies.get('visits')
        # Separate value and hash, check hash
        # if visit_cookie_str:
        #     salt = visit_cookie_str.split("|")[2]
        #     cookie_val = check_secure_withsalt(visit_cookie_str)
        #     if cookie_val:
        #         visits = int(cookie_val)
        # new_cookie_val = hash_str(str(visits), salt)
        # self.response.headers.add_header('Set-Cookie', 'visits=%s' % str(new_cookie_val))

        self.render_blog()


# Google sign-in effort I think.
# Identifying yoursef by changing a header's "User-Agent"
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



# Example of memecache, wasn't workind when top_arts
# called from NewPost(), because we were quering the database, before sending the POST request to store the new data. SO we were still getting the entities, not the most recent. Fixed by moving the memcache update to ArtivelView (next handler for both NewPost and EditPost.)
CACHE = {} # Temproary memcache example
def top_arts(update = False):
    key = 'top' # Will be the reference to the value we wil store here.
    if not update and key in CACHE:
        logging.warning("Getting CACHE")
        logging.warning("Update value: %s" % update)
        arts = CACHE[key]
        logging.warning("Length of arts: %s" % len(arts))
    else: # Query the database
        logging.warning("Running a DB Query == Moneyyyy!")
        # arts = Articles.all().order('-created') # Old db
        arts = Articles.query().order(-Articles.created) # new ndb
        arts = list(arts) # Avoids querying the db again in jinja template!
        # CACHE.clear()
        CACHE[key] = arts
        logging.warning("Length of arts after re-query: %s" % len(arts))
        logging.warning("Length of CACHE[key] after re-query: %s" % len(CACHE[key]))
    return arts
