#!/usr/bin/env python
"""
A simple HTTP server to execute ABS prgorams.
Examples for sending requests:
    curl -F "--help=" http://localhost:9001
    curl -F "abs=@<FILE>" "abs1=@<FILE>" ... http://localhost:9001/process
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import urllib.parse as urlparse
import logging
import cgi
import tempfile
import os
import subprocess
import click
import shutil

# default timeout in seconds
COMPILATION_TIMEOUT = 300
ABS_EXECUTION__TIMEOUT = 3600
LOG_PARSING_TIMEOUT = 300


class MyServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        '''
        Handle GET requests.
        '''
        logging.debug('GET {}'.format(self.path))
        if urlparse.urlparse(self.path).path == "/health":
            self._set_headers()
            self.wfile.write("OK\n".encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        '''
        Handle POST requests.
        '''
        logging.debug('POST {}'.format(self.path))

        ctype, pdict = cgi.parse_header(self.headers['content-type'])

        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")

        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        else:
            postvars = {}

        if urlparse.urlparse(self.path).path == "/process":
            try:
                abs_prog = []
                python_prog = []
                extra_param = []
                temp_dir = tempfile.mkdtemp()
                extra_files = []

                for i in postvars:
                    if i == 'abs':
                        logging.debug("Found {} abs input files".format(len(postvars[i])))
                        for j in postvars[i]:
                            file_id, name = tempfile.mkstemp(suffix='.abs')
                            os.close(file_id)
                            with open(name, "w") as f:
                                f.write(j.decode("utf-8"))
                            abs_prog.append(name)
                    elif i == 'log_parser':
                        if len(postvars[i]) != 1:
                            raise ValueError("Zero or more than one log_parser programs sent")
                        logging.debug("Found log_parser input file")
                        file_id, name = tempfile.mkstemp(suffix='.py')
                        os.close(file_id)
                        with open(name,"w") as f:
                            f.write(postvars[i][0].decode("utf-8"))
                        python_prog.append(name)
                    else:
                        if len(postvars[i]) > 1:
                            raise ValueError("Parameter {} badly formatted".format(i))
                        if postvars[i][0] == "":
                            logging.debug("Found flag {}".format(i))
                            extra_param.append(i)
                        else:
                            logging.debug("Found parameter {} with value {}".format(i, postvars[i]))
                            extra_param.append(i)
                            extra_param.append(postvars[i][0])

                if not abs_prog:
                    raise ValueError("No ABS program found")

                logging.debug('Compiling the model')
                cmd = ["timeout", str(COMPILATION_TIMEOUT), "absc", "-erlang"] + abs_prog
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=temp_dir)
                out, err = proc.communicate()
                #logging.debug('Stdout of abs compilation: {}'.format(out))
                logging.debug('Stderr of abs compilation: {}'.format(err))
                if proc.returncode != 0:
                    raise ValueError("Compilation of ABS program ended up with return code {}".format(proc.returncode))

                logging.info('Running model in directory {}'.format(temp_dir))
                cmd = ["timeout", str(ABS_EXECUTION__TIMEOUT), "./gen/erl/run"] + extra_param
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=temp_dir)
                out, err = proc.communicate()
                #logging.debug('Stdout of abs compilation: {}'.format(out))
                logging.debug('Stderr of abs compilation: {}'.format(err))
                if proc.returncode != 0:
                    raise ValueError(
                        "Execution of ABS program ended up with return code {}".format(proc.returncode))

                if python_prog:
                    # save output in a file
                    file_id, file_name = tempfile.mkstemp(text=True)
                    extra_files.append(name)
                    os.write(file_id,out)
                    os.close(file_id)

                    logging.info('Parsing output')
                    cmd = ["timeout", str(LOG_PARSING_TIMEOUT), "python", python_prog[0], file_name]
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=temp_dir)
                    out, err = proc.communicate()
                    #logging.debug('Stdout of abs compilation: {}'.format(out))
                    logging.debug('Stderr of output parse execution: {}'.format(err))
                    if proc.returncode != 0:
                        raise ValueError(
                            "Parsing of the output of the ABS program ended up with return code {}".format(
                                proc.returncode))
                self._set_headers()
                self.wfile.write(out)
            except ValueError as e:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write("Error: {}".format(e).encode('utf-8'))

            finally:
                # delete files and directory
                for i in abs_prog + python_prog + extra_files:
                    if os.path.exists(i):
                        os.remove(i)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("Operation not allowed".encode('utf-8'))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

def run(port=9001):
    server_address = ('localhost', port)
    server = ThreadedHTTPServer(server_address, MyServer)
    logging.info('Starting httpd server...')
    server.serve_forever()


@click.command()
@click.option('--port', '-p', type=click.INT, default=9001,
              help='Port used by the server to wait for requests.')
@click.option('--log-level',
              help='Log level',
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
              default="DEBUG",
              show_default=True)
def main(port,log_level):
    logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s]%(message)s",
                        level=log_level)
    run(port=port)


if __name__ == "__main__":
    main()