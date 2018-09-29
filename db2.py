import sys
import uuid
import cgi
import posixpath 
import sys, traceback
 
# python 2x & 3x compatability
if sys.version_info[0] >= 3:
    from http.server import BaseHTTPRequestHandler,HTTPServer
    from html import escape
    from urllib import parse
    parser = parse
    def print_bytes(str):
        return bytes(str, 'utf-8')
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from cgi import escape
    import urlparse
    parser = urlparse
    def print_bytes(str):
        return bytes(str)
 
from dropbox import DropboxOAuth2Flow
import dropbox
 
# simple memory sessions
sessions = {}
 
port = 8088
root = "http://localhost"
 
def get_dropbox_auth_flow(web_app_session):
    return DropboxOAuth2Flow( "y9r9coydrlppgmc", "qfapyf1vjfmvhk5", root+":"+str(port), web_app_session, "dropbox-auth-csrf-token")
 
def process_folder_entries(current_state, entries):
    for entry in entries:
        if isinstance(entry, dropbox.files.DeletedMetadata):
            current_state.pop(entry.path_lower, None)
        else:
            current_state[entry.path_lower] = entry
    return current_state
     
class MyApp(BaseHTTPRequestHandler):
     
    def oauth(self, query):
        session = None;        
        if 'cookie' in self.headers and self.headers['cookie'] in sessions:
            session = sessions[self.headers['cookie']]
  
        # Check if we're coming back from an OAuth flow with the 'code' param. Make a request if so
        if 'code' in query:
            oauth_result = get_dropbox_auth_flow(session).finish(query)
            session['bearer_token'] = oauth_result.access_token
            self.send_response(302)
            self.send_header('Location', root+":"+str(port))
            self.end_headers()
            return None
 
        #  If we're not logged in, redirect start OAuth flow
        if session is None or 'bearer_token' not in session:
           self.send_response(302)
           if session is None:
               session_id = uuid.uuid4().hex
               sessions[session_id] = {}
               session = sessions[session_id]
               self.send_header('Set-Cookie', session_id)
           self.send_header('Location', get_dropbox_auth_flow(session).start())
           self.end_headers()
           return None
         
        return session        
     
    def do_GET(self):
        try:
            query = dict(parser.parse_qsl(self.path[2:]))
             
            #Handle oauth
            session = self.oauth(query)
            if session is None:
                return;
   
            # connect to account
            dbx = dropbox.Dropbox(session['bearer_token'])
            # thumbnail render
            if ('action' in query and query['action'] == 'thumb'):
                self.send_response(200)
                self.send_header('Content-type', 'binary')
                self.end_headers()             
                thumb_md, thumb = dbx.files_get_thumbnail(query['path'])
                self.wfile.write(thumb.content)
                return
             
            # render directory
            body = "<h1>Welcome, "+dbx.users_get_current_account().name.display_name+"</h1>"
             
            # get path from query string
            body += "<h2>Here are your expenses "
            path=""
            if 'path' in query:
                path = query['path']
                body += "<h3>"+path+"</h3>"+'<a href="'+escape(root+':'+str(port))+'">(back)</a/>'
            body += "</h2>"
 
            # get all files
            result = dbx.files_list_folder(path=path, limit=5)
            files = process_folder_entries({}, result.entries)
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                files = process_folder_entries(files, result.entries)
 
            # render list of files
            hasFile = False
            body += "<ul>"
            for file in files.values():
                if isinstance(file, dropbox.files.FolderMetadata):
                    body += '<li><a href="'+escape(root+':'+str(port)+'?path='+file.path_lower)+'">'+file.name+'</a></li>'
                else:
                    thumb = '<img src="'+escape(root+':'+str(port)+'?path='+file.path_lower)+'&action=thumb">' if not file.path_lower.endswith('zip') else ''
                    hasFile = True
                    # If organize was clicked, move the files
                    if ('action' in query and query['action'] == 'organize'):
                        destination_path = posixpath.join("/" + str(file.client_modified.year) + "_Expenses", str(file.client_modified.month), file.name)
                        if file.path_lower != destination_path.lower():
                            dbx.files_move_v2(file.path_lower, destination_path)
                        body += '<li>'+file.name+' - moved to '+destination_path+'</li>'
                    # Else just show the filename
                    else: 
                        body += '<li>'+thumb+file.name+'</li>'
            body += "</ul>"
         
            if hasFile:
                body += '<b><a href="'+escape(root+':'+str(port)+ ( ('?path='+query['path']+'&') if 'path' in query else '?' ) )+'action=organize">Organize</a></b>'
               
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()             
            self.wfile.write(print_bytes('<html><body>'+body+'</body></html>'))
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()             
            self.wfile.write(print_bytes("<b>Exception:</b>"))
            self.wfile.write(print_bytes(str(e)))
    
def run(server_class=HTTPServer, handler_class=MyApp, port=port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Server running at '+root+':'+str(port)+'...')
    httpd.serve_forever()
 
run()