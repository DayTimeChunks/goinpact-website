

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
