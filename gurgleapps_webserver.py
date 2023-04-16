"""
    Project: GurgleApps Web Server
    File: gurgleapps_webserver.py
    Author: GurgleApps.com
    Date: Your Date 2023-04-01
    Description: GurgleApps Web Server
"""
import network
import re
import time
import uos
import uasyncio as asyncio
import ujson as json
from response import Response
from request import Request
import gc
import os


class GurgleAppsWebserver:

#    def __init__(self, wifi_ssid, wifi_password, port=80, timeout=20, doc_root="/www", log_level=0):
    def __init__(self, port=80, doc_root="/www", log_level=0):
        print("GurgleApps.com Webserver")
        self.port = port
        self.doc_root = doc_root
        self.function_routes = []
        self.log_level = log_level
        # wifi client in station mode so we can connect to an access point
        self.html = """<!DOCTYPE html>
        <html>
            <head> <title>GurgleApps.com Webserver</title> </head>
            <body> <h1>Pico W</h1>
                <p>%s</p>
            </body>
        </html>
        """
        # asyncio.new_event_loop()
        print("exit constructor")

    # async def start_server(self):
    #     print("start_server")
    #     asyncio.create_task(asyncio.start_server(
    #         self.serve_request, "0.0.0.0", 80))
    #     while self.serving:
    #         await asyncio.sleep(0.1)

    async def start_server(self):
        print("start_server")
        server_task = asyncio.create_task(asyncio.start_server(
            self.serve_request, "0.0.0.0", 80))
        await server_task

    # async def start_server(self):
    #     print("start_server")
    #     server = await asyncio.start_server(
    #         self.serve_request, "0.0.0.0", 80)
    #     async with server:
    #         await server.serve_forever()

    def add_function_route(self, route, function):
        self.function_routes.append({"route": route, "function": function})

    async def serve_request(self, reader, writer):
        gc.collect()
        try:
            url = ""
            method = ""
            content_length = 0
            # Read the request line by line because we want the post data potentially
            headers = []
            post_data = None
            while True:
                line = await reader.readline()
                # print("line: "+str(line))
                line = line.decode('utf-8').strip()
                if line == "":
                    break
                headers.append(line)
            request_raw = str("\r\n".join(headers))
            print(request_raw)
            request_pattern = re.compile(r"(GET|POST)\s+([^\s]+)\s+HTTP")
            match = request_pattern.search(request_raw)
            if match:
                method = match.group(1)
                url = match.group(2)
                print(method, url)
            else:  # regex didn't match, try splitting the request line
                request_parts = request_raw.split(" ")
                if len(request_parts) > 1:
                    method = request_parts[0]
                    url = request_parts[1]
                    print(method, url)
                else:
                    print("no match")
            # extract content length for POST requests
            if method == "POST":
                content_length_pattern = re.compile(r"Content-Length:\s+(\d+)")
                match = content_length_pattern.search(request_raw)
                if match:
                    content_length = int(match.group(1))
                    print("content_length: "+str(content_length))
            # Read the POST data if there's any
            if content_length > 0:
                post_data_raw = await reader.readexactly(content_length)
                print("POST data:", post_data_raw)
                post_data = json.loads(post_data_raw)
            request = Request(post_data)
            response = Response(writer)
            # check if the url is a function route and if so run the function
            path_components = self.get_path_components(url)
            print("path_components: "+str(path_components))
            route_function, params = self.match_route(path_components)
            if route_function:
                print("calling function: "+str(route_function) +
                      " with params: "+str(params))
                await route_function(request, response, *params)
                return
            # perhaps it is a file
            file_path = self.doc_root + url
            if self.log_level > 0:
                print("file_path: "+str(file_path))
            # if uos.stat(file_path)[6] > 0:
            if self.file_exists(file_path):
                content_type = self.get_content_type(url)
                if self.log_level > 1:
                    print("content_type: "+str(content_type))
                await response.send_file(file_path, content_type=content_type)
                return
            if url == "/":
                print("root")
                files_and_folders = self.list_files_and_folders(self.doc_root)
                await response.send_iterator(self.generate_root_page_html(files_and_folders))
                return
                html = self.generate_root_page_html(files_and_folders)
                await response.send(html)
                return
            print("file not found "+url)
            await response.send(self.html % "page not found "+url, status_code=404)
            if (url == "/shutdown"):
                self.serving = False
        except OSError as e:
            print(e)

    def dir_exists(self, filename):
        try:
            return (os.stat(filename)[0] & 0x4000) != 0
        except OSError:
            return False

    def file_exists(self, filename):
        try:
            return (os.stat(filename)[0] & 0x4000) == 0
        except OSError:
            return False

    def get_file(self, filename):
        print("getFile: "+filename)
        try:
            # Check if the file exists
            if uos.stat(filename)[6] > 0:
                # Open the file in read mode
                with open(filename, "r") as f:
                    # Read the contents of the file into a string
                    return f.read()
            else:
                # The file doesn't exist
                return False
        except OSError as e:
            # print the error
            print(e)
            return False

    def get_path_components(self, path):
        print("get_path_components: "+path)
        return tuple(filter(None, path.split('/')))

    def match_route(self, path_components):
        for route in self.function_routes:
            route_pattern = list(filter(None, route["route"].split("/")))
            if self.log_level > 1:
                print("route_pattern: "+str(route_pattern))
            if len(route_pattern) != len(path_components):
                continue
            match = True
            params = []
            for idx, pattern_component in enumerate(route_pattern):
                if self.log_level > 2:
                    print("pattern_component: "+str(pattern_component))
                if pattern_component.startswith('<') and pattern_component.endswith('>'):
                    param_value = path_components[idx]
                    params.append(param_value)
                else:
                    if pattern_component != path_components[idx]:
                        match = False
                        break
            if match:
                return route["function"], params
        return None, []

    def get_file_extension(self, file_path):
        file_parts = file_path.split('.')
        if len(file_parts) > 1:
            return file_parts[-1]
        return ''

    def get_content_type(self, file_path):
        extension = self.get_file_extension(file_path)
        content_type_map = {
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'ico': 'image/x-icon',
            'svg': 'image/svg+xml',
            'json': 'application/json',
            'xml': 'application/xml',
            'pdf': 'application/pdf',
            'zip': 'application/zip',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'mp3': 'audio/mpeg',
            'mp4': 'video/mp4',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'webm': 'video/webm',
        }
        return content_type_map.get(extension, 'text/plain')

    def list_files_and_folders(self, path):
        entries = uos.ilistdir(path)
        files_and_folders = []
        for entry in entries:
            name = entry[0]
            mode = entry[1]
            if mode & 0o170000 == 0o040000:  # Check if it's a directory
                files_and_folders.append({"name": name, "type": "directory"})
            elif mode & 0o170000 == 0o100000:  # Check if it's a file
                files_and_folders.append({"name": name, "type": "file"})
        return files_and_folders

    def generate_root_page_html(self, files_and_folders):
        yield """
       <!DOCTYPE html>
        <html>
            <head>
                <title>GurgleApps.com Webserver</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="/styles.css" rel="stylesheet">
            </head>
            <body class="bg-gray-100">
        """
        yield """
        <div class="relative flex min-h-screen flex-col justify-center overflow-hidden bg-gray-50 py-6 sm:py-12">
        <div class="relative bg-white px-6 pb-8 pt-10 shadow-xl ring-1 ring-gray-900/5 sm:mx-auto sm:max-w-lg sm:rounded-lg sm:px-10">
        <div class="mx-auto max-w-md">
        <img src="/img/logo.svg" class="h-12 w-auto" alt="GurgleApps.com">
        """
        yield """
        <div class="divide-y divide-gray-300/50">
        <div class="space-y-6 py-8 text-base leading-7 text-gray-600">
          <h1 class="text-lg font-semibold">Welcome to GurgleApps.com Webserver</h1>
          <h12 class="text-base font-semibold">File List:</h2>
          <ul class="space-y-2 mt-3">
        """
        folder_icon_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6  fill-indigo-800">
        <path d="M19.5 21a3 3 0 003-3v-4.5a3 3 0 00-3-3h-15a3 3 0 00-3 3V18a3 3 0 003 3h15zM1.5 10.146V6a3 3 0 013-3h5.379a2.25 2.25 0 011.59.659l2.122 2.121c.14.141.331.22.53.22H19.5a3 3 0 013 3v1.146A4.483 4.483 0 0019.5 9h-15a4.483 4.483 0 00-3 1.146z" />
        </svg>
        """
        file_icon_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6 fill-indigo-800">
        <path d="M5.625 1.5c-1.036 0-1.875.84-1.875 1.875v17.25c0 1.035.84 1.875 1.875 1.875h12.75c1.035 0 1.875-.84 1.875-1.875V12.75A3.75 3.75 0 0016.5 9h-1.875a1.875 1.875 0 01-1.875-1.875V5.25A3.75 3.75 0 009 1.5H5.625z" />
        <path d="M12.971 1.816A5.23 5.23 0 0114.25 5.25v1.875c0 .207.168.375.375.375H16.5a5.23 5.23 0 013.434 1.279 9.768 9.768 0 00-6.963-6.963z" />
        </svg>
        """
        for file_or_folder in files_and_folders:
            icon = folder_icon_svg if file_or_folder['type'] == 'directory' else file_icon_svg
            yield f"<li class='border-t pt-1'><a href='/{file_or_folder['name']}' class='flex items-center font-semibold text-slate-800 hover:text-indigo-800'>{icon}<p class='ml-2'>{file_or_folder['name']}</p></a></li>"
        yield "</ul>"
        # Closing tags for the body and container div
        yield """
        </div>
        <div class="pt-3 text-base font-semibold leading-7">
        <p class="text-gray-900">More information</p><p><a href="https://gurgleapps.com/learn/projects/micropython-web-server-control-raspberry-pi-pico-projects" class="text-indigo-500 hover:text-sky-600">Project Home &rarr;</a>
        </p></div></div></div></div></div></body></html>
        """
       

