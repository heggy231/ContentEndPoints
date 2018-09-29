import dropbox
import posixpath
from dropbox import DropboxOAuth2FlowNoRedirect
import sys 

auth_flow = DropboxOAuth2FlowNoRedirect("APP_KEY", "APP_SECRET")
print("Authorize your script here: "+auth_flow.start())
code = raw_input('Input your code: ').strip()

print("Initializing Dropbox API...")
dbx = dropbox.Dropbox(auth_flow.finish(code).access_token)

# print("Initializing Dropbox API...")
# dbx = dropbox.Dropbox("_g3rh767bdUAAAAAAAAQ3JIPgpil68H_3RhDCBZvIaUqraTL6lb6VA2xOfK4SN9t")


# for entry in result.entries:
#     print(entry.name+", modified "+entry.client_modified.strftime('%Y-%m-%d'))


def process_folder_entries(current_state, entries):
    for entry in entries: # loop that goes through entries
        if isinstance(entry, dropbox.files.FileMetadata): # FileMetadata is state update about file
            current_state[entry.path_lower] = entry
        elif isinstance(entry, dropbox.files.DeletedMetadata):
            current_state.pop(entry.path_lower, None) # ignore KeyError if missing
    return current_state

print("Scanning for expense files...")
result = dbx.files_list_folder(path="/Sample Expenses", limit=5)
files = process_folder_entries({}, result.entries)

for entry in files.values():
    print(entry.name + ", modified "+entry.client_modified.strftime('%Y-%m-%d'))
# The result may be different order if that matters add sorting step

## 

print("Scanning for expense files...")
result = dbx.files_list_folder(path="/Sample Expenses", limit=5)
files = process_folder_entries({}, result.entries)

# follow the cursor until we've collected all results
while result.has_more:
    print("Collecting additional files...")
    result = dbx.files_list_folder_continue(result.cursor)
    files = process_folder_entries(files, result.entries)


#########
for entry in files.values():
    # use modified time of file to build destination path
    destination_path = posixpath.join(
        "/" + str(entry.client_modified.year) + "_Expenses",
        str(entry.client_modified.month),
        entry.name
    )
    print("Moving {} to {}".format(entry.path_display, destination_path))
    dbx.files_move_v2(entry.path_lower, destination_path)



# python 2x & 3x compatability
if sys.version_info[0] >= 3:
    from http.server import BaseHTTPRequestHandler,HTTPServer
    def print_bytes(str):
        return bytes(str, 'utf-8')
else:    
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    def print_bytes(str):
        return bytes(str)

port = 8088
root = "http://localhost"

class MyApp(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()            
        self.wfile.write(print_bytes('<html><body>Hello, world</body></html>'))
  
def run(server_class=HTTPServer, handler_class=MyApp, port=port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Server running at '+root+':'+str(port)+'...')
    httpd.serve_forever()
  
run()



# Notes: https://paper.dropbox.com/doc/SF-DBX-Dev-Workshop-Guide-Getting-Started-with-the-Dropbox-API--ANRhVct9g4DcCwi1XJx5QGmxAg-CQExilGxVruQh0EO2mdJ6
