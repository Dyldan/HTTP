import os
import socket
import json

class HTTPServer:

    ##################################################
    ###################### DICTS #####################
    ##################################################

    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented',
    }

    headers = {
        'Server': 'HTTP_users',
        'Content-Type': 'application/json',
    }

    ##################################################
    #################### MAIN FLOW ###################
    ##################################################

    def __init__(self, host = '127.0.0.1', port = 8888):
        self.host = host
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)

        print("Listening at", s.getsockname())

        while True:
            conn, addr = s.accept()
            print("Connected by", addr)
            data = conn.recv(8192)

            response = self.handle_request(data)

            conn.sendall(response)
            conn.close()

    def handle_request(self, data):
        request = HTTPRequest(data)

        try:
            handler = getattr(self, 'handle_%s' % request.method)
        except:
            handler = self.HTTP_501_handler

        response = handler(request)

        return response
    
    ##################################################
    ################ RESPONSE BUILDERS ###############
    ##################################################

    def response_line(self, status_code):
        reason = self.status_codes[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)

        return line.encode()
    
    def response_headers(self, extra_headers = None):
        headers_copy = self.headers.copy()

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ""

        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])

        return headers.encode()
    
    ##################################################
    ################# ERROR HANDLERS #################
    ##################################################

    def HTTP_501_handler(self, request):
        response_line = self.response_line(status_code = 501)
        response_headers = self.response_headers()
        blank_line = b"\r\n"
        response_body = b"501 Not Implemented"
        response = b"".join([response_line, response_headers, blank_line, response_body])

        return response

    ##################################################
    ################ METHOD HANDLERS #################
    ##################################################

    def handle_GET(self, request):
        
        fn = request.uri.strip('/')
        
        if os.path.exists(fn):
            response_line = self.response_line(status_code = 200)
            response_headers = self.response_headers()
            with open(fn, 'rb') as f:
                response_body = f.read()
        else:
            response_line = self.response_line(status_code = 404)
            response_headers = self.response_headers()
            response_body = b"404 Not Found"
        
        blank_line = b"\r\n"

        response = b"".join([response_line, response_headers, blank_line, response_body])
        
        return response
    
    def handle_POST(self, request):
        
        valid_id = False
        valid_name = False

        new_user = {
            "user_id": "ERROR",
            "name": "ERROR"
        }

        for line in request.body:
            line = line.decode("UTF-8")
            parts = line.split(": ")

            if parts[0] == 'user_id' and parts[1] != '':
                new_user.update({"user_id": parts[1]})
                valid_id = True
            elif parts[0] == 'name' and parts[1] != '':
                new_user.update({"name": parts[1]})
                valid_name = True

        if valid_id and valid_name:
            response_line = self.response_line(status_code = 200)
            response_headers = self.response_headers()
            response_body = b"User Added"

            with open('users.json','r+') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)
                # Join new_data with file_data inside emp_details
                file_data["users"].append(new_user)
                # Sets file's current position at offset.
                file.seek(0)
                # Convert back to json.
                json.dump(file_data, file, indent = 4)

        else:
            response_line = self.response_line(status_code = 404)
            response_headers = self.response_headers()
            response_body = b"404 Not Found"

        blank_line = b"\r\n"

        response = b"".join([response_line, response_headers, blank_line, response_body])

        return response
    
    def handle_DELETE(self, request):
        
        user_id = None
        is_valid_id = False

        if len(request.body) == 1:
            user_id = request.body[0]
            user_id = user_id.decode("UTF-8")
            
            with open('users.json', 'r+') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)
                # Clear content or code breaks lol
                file.truncate(0)
                # Delete specified user
                for i, user in enumerate(file_data["users"]):
                    if user["user_id"] == user_id:
                        file_data["users"].pop(i)
                        is_valid_id = True
                # Sets file's current position at offset.
                file.seek(0)
                # Convert back to json.
                json.dump(file_data, file, indent = 4)

        if is_valid_id:
            response_line = self.response_line(status_code = 200)
            response_headers = self.response_headers()
            response_body = b"User Deleted"
        else:
            response_line = self.response_line(status_code = 404)
            response_headers = self.response_headers()
            response_body = b"404 Not Found"

        blank_line = b"\r\n"

        response = b"".join([response_line, response_headers, blank_line, response_body])

        return response
    
    def handle_PUT(self, request):
        with open('users.json', 'r+') as file:
            # Erase file
            file.truncate(0)
            # Sets file's current position at offset.
            file.seek(0)
            # Write the new data
            file_data = ''
            for x in request.body:
                file_data += x.decode("UTF-8") + '\n'
            file.write(file_data)

        
        response_line = self.response_line(status_code = 200)
        response_headers = self.response_headers()
        response_body = b"Yurrr"

        blank_line = b"\r\n"

        response = b"".join([response_line, response_headers, blank_line, response_body])

        return response



class HTTPRequest:

    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = '1.1'
        self.headers = None
        self.body = None
        self.parse(data)

    def parse(self, data):
        lines = data.split(b"\r\n")
        blank_line_idx = -1
        
        # request_line
        request_line = lines[0]
        words = request_line.split(b" ")

        self.method = words[0].decode()

        if len(words) > 1:
            self.uri = words[1].decode()

        if len(words) > 2:
            self.http_version = words[2]

        # request_headers
        request_headers = []
        for i, line in enumerate(lines):
            if i == 0:
                continue
            elif line == b'':
                blank_line_idx = i
                break

            request_headers.append(line)

        self.headers = request_headers

        # request_body
        request_body = []
        for i in range(blank_line_idx+1, len(lines)):
            # Some weird bs where if a newline doesn't include \r then I have to split over just \n
            if '\n' in lines[i].decode("UTF-8"):
                temp = lines[i].decode("UTF-8")
                new_lines = temp.split('\n')
                for nl in new_lines:
                    request_body.append(nl.encode())
            else:
                request_body.append(lines[i])

        self.body = request_body

        # Print entire request
        # print(request_line.decode("UTF-8"))
        # for r in request_headers:
        #     print(r.decode("UTF-8"))
        # for r in request_body:
        #     print(r.decode("UTF-8"))

        # Print entire request
        # for line in lines:
        #     print(line.decode("UTF-8"))
    


# Start the server
server = HTTPServer()
server.start()