
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
