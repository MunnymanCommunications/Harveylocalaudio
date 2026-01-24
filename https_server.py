#!/usr/bin/env python3
"""
Simple HTTPS server for Harvey IO
Enables microphone access on Safari mobile
"""
import http.server
import ssl
import os

# Change to the directory containing harvey_io.html
os.chdir('/home/nic/Harveylocalaudio')

# Create server
server_address = ('0.0.0.0', 8443)
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

# Setup SSL
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    certfile='ssl/cert.pem',
    keyfile='ssl/key.pem'
)

httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)

print('=' * 60)
print('🔒 HTTPS Server Started!')
print('=' * 60)
print(f'Local access:     https://localhost:8443/harvey_io.html')
print(f'Network access:   https://192.168.4.108:8443/harvey_io.html')
print('=' * 60)
print('IMPORTANT: You must trust the certificate on your device!')
print('See instructions after server starts.')
print('=' * 60)
print()

httpd.serve_forever()
