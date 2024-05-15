#!/usr/bin/python
import time
import datetime
import numpy
import random
import gzip
import sys
import argparse
from faker import Faker
from tzlocal import get_localzone
local = get_localzone()

#todo:
# allow writing different patterns (Common Log, Apache Error log etc)
# log rotation


class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

parser = argparse.ArgumentParser(__file__, description="Fake Apache Log Generator")
parser.add_argument("--output", "-o", dest='output_type', help="Write to a Log file, a gzip file or to STDOUT", choices=['LOG','GZ','CONSOLE'] )
parser.add_argument("--log-format", "-l", dest='log_format', help="Log format, Common or Extended Log Format ", choices=['CLF','ELF'], default="ELF" )
parser.add_argument("--num", "-n", dest='num_lines', help="Number of lines to generate (0 for infinite)", type=int, default=1)
parser.add_argument("--prefix", "-p", dest='file_prefix', help="Prefix the output file name", type=str)
parser.add_argument("--sleep", "-s", help="Sleep this long between lines (in seconds)", default=0.0, type=float)

args = parser.parse_args()

log_lines = args.num_lines
file_prefix = args.file_prefix
output_type = args.output_type
log_format = args.log_format

faker = Faker()

timestr = time.strftime("%Y%m%d-%H%M%S")
otime = datetime.datetime.now()

outFileName = 'access_log_'+timestr+'.log' if not file_prefix else file_prefix+'_access_log_'+timestr+'.log'

for case in switch(output_type):
    if case('LOG'):
        f = open(outFileName,'w')
        break
    if case('GZ'):
        f = gzip.open(outFileName+'.gz','w')
        break
    if case('CONSOLE'): pass
    if case():
        f = sys.stdout

response=["200","404","301","500", None]

verb=["GET","POST","DELETE","PUT"]

resources=["/list","/wp-content","/wp-admin","/explore","/search/tag/list","/app/main/posts","/posts/posts/explore","/apps/cart.jsp?appID="]

ualist = [faker.firefox, faker.chrome, faker.safari, faker.internet_explorer, faker.opera]

ip_list = [faker.ipv4() for _ in range(1000)]

def comprueba_noche(dt):
    empieza_noche = 22
    empieza_dia = 7
    
    return dt.hour > empieza_noche or dt.hour < empieza_dia

def randomResponsePareto():
    alpha = 2.5
    indice = int(random.paretovariate(alpha)) - 1
    indice = min(indice, 3)
    return response[indice]


flag = True
while (flag):

    resp = randomResponsePareto()
    if not resp:
        continue

    if args.sleep:
        increment = datetime.timedelta(seconds=args.sleep)
    else:
        es_noche = comprueba_noche(otime)
        rango_min = 90 if es_noche else 30
        rango_max = 500 if es_noche else 300
        increment = datetime.timedelta(seconds=random.randint(rango_min, rango_max))
    otime += increment

    ip = random.choice(ip_list)
    dt = otime.strftime('%d/%b/%Y:%H:%M:%S')
    tz = datetime.datetime.now(local).strftime('%z')
    vrb = numpy.random.choice(verb,p=[0.6,0.1,0.1,0.2])

    uri = numpy.random.choice(resources, p=[0.184, 0.029, 0.029, 0.29, 0.117, 0.117, 0.117, 0.117])
    if uri.find("apps")>0:
        uri += str(random.randint(1000,10000))

    byt = int(random.gauss(5000,50))
    referer = faker.uri()
    useragent = numpy.random.choice(ualist,p=[0.5,0.3,0.1,0.05,0.05] )()
    if log_format == "CLF":
        f.write('%s - - [%s %s] "%s %s HTTP/1.0" %s %s\n' % (ip,dt,tz,vrb,uri,resp,byt))
    elif log_format == "ELF": 
        f.write('%s - - [%s %s] "%s %s HTTP/1.0" %s %s "%s" "%s"\n' % (ip,dt,tz,vrb,uri,resp,byt,referer,useragent))
    f.flush()

    log_lines = log_lines - 1
    flag = False if log_lines == 0 else True
    if args.sleep:
        time.sleep(args.sleep)
