#!/usr/bin/env python

import subprocess


out = subprocess.Popen(['links', '-dump', 'www.google.com'],
stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)

stdout,stderr = out.communicate()
print(stdout)