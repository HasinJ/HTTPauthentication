import socket
import signal
import sys
import random

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)
hostname = socket.gethostname()
print(hostname)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://localhost:%d" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
""" % port

# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form

# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form

# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form


# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://localhost:%d" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
""" % port


#### Helper functions
def parseBody(users, secrets, body):
    # type: (dict, dict, str) -> (str)

    """
    If exactly one among the username or password fields is absent in the entity body (i.e., exactly one field is present),
    or if both fields are present but the username is not in the passwords file,
    or the password did not match the corresponding username in the passwords file,

    then we ask the user to log in again.
    """

    if "&" in body:
        words = body.split("&")
        if len(words) != 2: return
        key = None
        value = None

        words[0] = words[0].split("=")
        if words[0][0] == "username": key = words[0][1]
        elif words[0][0] == "password": value = words[0][1]

        words[1] = words[1].split("=")
        if words[1][0] == "username": key = words[1][1]
        elif words[1][0] == "password": value = words[1][1]

        if (not value) or (not key): return
        if key in users:
            if users[key] != value: return
        else: return

        if key in secrets: return secrets[key]
        else: return


def parseHeaders(headers):
    list = headers.split("Cookie: token=")
    if(len(list) == 1):
        return
    else: return list[1]


# Printing.
def print_value(tag, value):
    print "Here is the", tag
    print "\"\"\""
    print value
    print "\"\"\""
    print

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)


# TODO: put your application logic here!
# Read login credentials for all the users
# Read secret data of all the users
# Send file lines to the server
loginfile = open('passwords.txt', 'r+')
users = {}
lines = loginfile.readlines()
for line in lines:
    line = line.strip().split()
    users[line[0]] = line[1]

secretfile = open('secrets.txt','r+')
secrets = {}
lines = secretfile.readlines()
for line in lines:
    line = line.strip().split()
    secrets[line[0]] = line[1]

count=0
cookies = {}
### Loop to accept incoming HTTP connections and respond.
while True:
    client, addr = sock.accept()
    req = client.recv(1024)

    # Let's pick the headers and entity body apart
    header_body = req.split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    print_value('headers', headers)
    print_value('entity body', body)

    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions
    headers_to_send = ''
    key = parseHeaders(headers)
    if(body == "action=logout" ):
        html_content_to_send = logout_page
        headers_to_send = 'Set-Cookie: token=; expires=Thu, 01 Jan 1970 00:00:00 GMT\r\n'
        cookies.clear()
    elif(key):
        print(key)
        if (key in cookies):
            html_content_to_send = cookies[key]
        else: html_content_to_send = bad_creds_page

    elif body == "username=&password=":
        html_content_to_send = login_page

    elif body:

        secret = parseBody(users, secrets, body)
        if secret:
            html_content_to_send = success_page + secret
            rand_val = random.getrandbits(64)
            cookies[str(rand_val)] = html_content_to_send
            headers_to_send = 'Set-Cookie: token=' + str(rand_val) + '\r\n'
        else: html_content_to_send = bad_creds_page


    # You need to set the variables:
    # (1) `html_content_to_send` => add the HTML content you'd like to send to the client.
    # Right now, we just send the default login page.
    else: html_content_to_send = login_page
    # But other possibilities exist, including
    # html_content_to_send = success_page + <secret>
    # html_content_to_send = bad_creds_page
    # html_content_to_send = logout_page

    # (2) `headers_to_send` => add any additional headers you'd like to send the client?
    # Right now, we don't send any extra headers.


    # Construct and send the final response
    response  = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)
    count+=1
    client.send(response)
    client.close()

    print "Served one request/connection! #{}\n\n".format(count)
    print

# We will never actually get here.
# Close the listening socket
sock.close()
