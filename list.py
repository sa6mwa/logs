#!/usr/bin/env python
# List QSOs in ADIF file(s)
# DE SA6MWA https://github.com/sa6mwa/sa6mwa-logs
# based on ADIF.PY by OK4BX http://web.bxhome.org
import sys, getopt, os
import re
import datetime
import time
import glob
ADIF_REC_RE = re.compile(r'<(.*?):(\d+).*?>([^<\t\f\v]+)')

def parse(fn):
  raw = re.split('<eor>|<eoh>(?i)', open(fn).read() )
  logbook =[]
  for record in raw[1:-1]:
    qso = {}
    tags = ADIF_REC_RE.findall(record)
    for tag in tags:
      qso[tag[0].lower()] = tag[2][:int(tag[1])]
    logbook.append(qso)    
  return logbook

def sortlogbook(data):
  for i in range(len(data)):
    # convert all entries into lower case and ensure qso_date and time_on exists
    data[i] = {k.lower(): v for k, v in data[i].items()}
    if 'qso_date' not in data[i]:
      data[i]['qso_date'] = ""
    if 'time_on' not in data[i]:
      data[i]['time_on'] = ""
  return sorted(data, key = lambda x: x['qso_date'] + x['time_on'])

def conv_datetime(adi_date, adi_time):
  return datetime.datetime.strptime(adi_date+adi_time.ljust(6,"0"), "%Y%m%d%H%M%S")

def compareQSO(qso1, qso2):
  match_keys = [ "call", "mode", "band" ]
  qso1 = { k.lower(): v for k, v in qso1.items() }
  qso2 = { k.lower(): v for k, v in qso2.items() }
  match = True
  for qso in [ qso1, qso2 ]:
    assert "qso_date" in qso, "qso_date not in qso: {}".format(qso)
    assert "time_on" in qso, "time_on not in qso: {}".format(qso)
  for k in match_keys:
    for qso in [ qso1, qso2 ]:
      assert k in qso, "required key {} is not in qso: {}".format(k, qso)
    qso1time = conv_datetime(qso1["qso_date"], qso1["time_on"])
    qso2time = conv_datetime(qso2["qso_date"], qso2["time_on"])
    if qso1time != qso2time:
      match = False
    if qso1[k] != qso2[k]:
      match = False
  return match

def qso_not_in_logbook(qso, logbook, hours=0):
  # returns True if qso is not in logbook or if hours > 0, return False (as if
  # qso was in logbook) if qso is older than hours old
  retval = True
  if hours > 0:
    for k in [ "qso_date", "time_on" ]:
      assert k in qso, "required key {} is not in qso: {}".format(k, qso)
    after = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    qsotime = conv_datetime(qso["qso_date"], qso["time_on"])
    if qsotime < after:
      return False
  for lbqso in logbook:
    if compareQSO(qso, lbqso):
      retval = False
  return retval

def usage():
  print "usage: %s [-n, --no-sort] logfile1.adif [logfile2.adif...]" % sys.argv[0]

def main():
  try:
    opts, adifs = getopt.getopt(sys.argv[1:], "hn", ["help","no-sort"])
  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(2)
  sort = True
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    elif o in ("-n", "--no-sort"):
      sort = False
    else:
      assert False, "unhandled option"
  if len(adifs) < 1:
    usage()
    sys.exit(2)

  logbook = list()
  for f in adifs:
    flogbook = parse(f)
    for qso in flogbook:
      if qso_not_in_logbook(qso, logbook, hours=0):
        logbook.append(qso)
  if sort:
    logbook = sortlogbook(logbook)
  fieldtemplate =            "{:8s} {:8s} {:11s} {:6s} {:5s} {:10s} {:30s}"
  print fieldtemplate.format("# DATE","TIME","CALL","MODE","BAND","QRG","EMAIL")
  for qso in logbook:
    na = "N/A"
    print fieldtemplate.format( qso["qso_date"] if "qso_date" in qso else na,
                                qso["time_on"] if "time_on" in qso else na,
                                qso["call"] if "call" in qso else na,
                                qso["mode"] if "mode" in qso else na,
                                qso["band"] if "band" in qso else na,
                                qso["freq"] if "freq" in qso else na,
                                qso["email"] if "email" in qso else na,
                              )

if __name__ == '__main__':
  main()
