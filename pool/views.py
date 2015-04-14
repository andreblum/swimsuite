from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
import pymongo
import os
import time
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Create your views here.

mongo_host = os.environ['SWIMSUITE_MONGO_PORT_27017_TCP_ADDR']
mongo_port = int(os.environ['SWIMSUITE_MONGO_PORT_27017_TCP_PORT'])

c = pymongo.Connection(mongo_host, mongo_port)
db = c.swimsuite_database
p = db.posts
p.create_index('time')
e = db.events

def home(request):
    return HttpResponse('Hello, world')


def icon(request):
    return redirect('/static/swimsuite.png')

def todayfig(request):
    now = time.localtime()
    today = time.mktime((now[0], now[1], now[2], 0, 0, 0, 0, 0, -1))
    vals = p.find({'time': { '$gt': today }})

    t = []
    w = []
    r = []

    for i in vals:
        st = time.localtime(i['time'])
        t.append(datetime.datetime(st[0], st[1], st[2], st[3], st[4], st[5]))
        w.append(i['water'])
        r.append(i['roof'])

    dates = matplotlib.dates.date2num(t)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.axis()
    ax.format_xdata = matplotlib.dates.DateFormatter('%h')
    ax.plot_date(dates, w, '-')
    ax.plot_date(dates, r, '-')
    plt.grid(b=True, which='major', color='0.5', linestyle=':')
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    response= HttpResponse(mimetype='image/png')
    canvas.print_png(response)
    return response



def today(request):
    return HttpResponse('<img src="todayfig"/>')

def weekfig(request):
    now = time.localtime()
    today = time.mktime((now[0], now[1], now[2], 0, 0, 0, 0, 0, -1))
    lastweek=today-7*24*60*60

    vals = p.find({'time': { '$gt': lastweek }})

    t = []
    w = []
    r = []

    for i in vals:
        st = time.localtime(i['time'])
        t.append(datetime.datetime(st[0], st[1], st[2], st[3], st[4], st[5]))
        w.append(i['water'])
        r.append(i['roof'])

    dates = matplotlib.dates.date2num(t)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.axis()
    ax.format_xdata = matplotlib.dates.DateFormatter('%h')
    ax.plot_date(dates, w, '-')
    ax.plot_date(dates, r, '-')
    plt.grid(b=True, which='major', color='0.5', linestyle=':')
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    response= HttpResponse(mimetype='image/png')
    canvas.print_png(response)
    return response


def week(request):
    return HttpResponse('<img src="weekfig"/>')

def stats(request):

    # when was pump switched on today?
    now = time.localtime()
    today = time.mktime((now[0], now[1], now[2], 0, 0, 0, 0, 0, -1))
    vals = p.find({'$and': [ {'time': { '$gt': today }}, {'pump': { '$eq': True}} ]})
    pump_start = vals.sort('time', pymongo.ASCENDING).limit(1).next()['time']
    vals.rewind()
    pump_stop = vals.sort('time', pymongo.DESCENDING).limit(1).next()['time']
    print time.localtime(pump_start)
    print time.localtime(pump_stop)

    vals = p.find({'time': {'$gt': pump_start+10*60, '$lt': pump_stop }})
    mintemp = vals.sort('water', pymongo.ASCENDING).limit(1).next()['water']
    vals.rewind()
    maxtemp = vals.sort('water', pymongo.DESCENDING).limit(1).next()['water']

    print mintemp
    print maxtemp

    return HttpResponse('mintemp: %.2f maxtemp: %.2f' % (mintemp, maxtemp))

def status(request):
    t = get_template('status.html')

    last = p.find().sort('time', pymongo.DESCENDING).limit(1).next()
    print last
    if last['valve']:
        valve = 'aan'
    else:
        valve = 'uit'

    if last['pump']:
        pump = 'aan'
    else:
        pump = 'uit'

    c = Context({'time': time.ctime(last['time']), 'roof': '%.2f' % last['roof'],
                 'water': '%.2f' % last['water'],
                 'valve': valve, 'pump':pump})
    print c
    html = t.render(c)
    return HttpResponse(html)


def log(request):
    global e

    t = get_template('logs.html')
    events = e.find()
    s = ''
    for ev in events:
        s += time.ctime(ev['time'])
        s += '  '
        s += ev['event']
        s += '\n'

    c = Context({ 'logs': s})

    return HttpResponse(t.render(c))

def control(request):
    t = get_template('control.html')
    c = Context({})
    html = t.render(c)
    return HttpResponse(html)
