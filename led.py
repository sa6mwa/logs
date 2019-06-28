#!/usr/bin/env python
# lid.py - List & EDit QSOs in ADIF file(s)
# DE SA6MWA https://github.com/sa6mwa/sa6mwa-logs
# partly based on ADIF.PY by OK4BX http://web.bxhome.org
import sys, errno, getopt, os
import re
import datetime
import time

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

def save(fn, data):
  header = "Log: {}\nGenerated by SA6MWA list.py\nhttps://github.com/sa6mwa/sa6mwa-logs\nbased on ADIF.PY by OK4BX\nhttp://web.bxhome.org\n<EOH>\n".format(fn)
  if os.path.exists(fn):
    split = re.split('<eoh>(?i)', open(fn).read())
    if len(split) > 1:
      header = split[0] + '<EOH>\n'
  fh=open(fn,'w')
  fh.write(header)
  for qso in data:
    for key in sorted(qso):
      value = qso[key]
      fh.write('<%s:%i>%s ' % (key.upper(), len(value), value))
    fh.write('<EOR>\n')
  fh.close()

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
  print """usage: {prog} [options] logfile.adif [logfile.adif...]
  -n, --dry-run       Simulate -i -q -f changes (do not save logbook)
  -u, --unsorted      Do not sort logbook (by date and time)
  -i, --index index   For use with -f, -v or -q options - specify that you
                      want to manipulate logbook index
  -q, --qsl code      For use with -i, add or change value of QSL_RCVD
                      and/or QSL_SENT. code is one or more of...
                        r = QSL_RCVD=Y
                        n = QSL_RCVD=N
                        s = QSL_SENT=Y
                        q = QSL_SENT=Q
                      You can combine them, e.g: -q rs
  -f, --field x       For use with -i, specify that you want to modify ADIF
                      field x of QSO with index specified with -i
  -v, --value y       For use with -i, set the value of field specified with
                      -f above to y of QSO with index given with -i
EXAMPLES
  # Set TX_PWR field to 10 for QSOs number 34 and 35
  $ {prog} -i 34,35 -f tx_pwr -v 10 mylog1.adif mylog2.adif
  # Set QSL_RCVD to Y and QSL_SENT to Q for QSO number 2
  $ {prog} -i 2 -q rq mylog1.adif mylog2.adif
""".format(prog=sys.argv[0])

def main():
  try:
    opts, adifs = getopt.getopt(sys.argv[1:], "hnui:q:f:v:", ["help","dry-run","unsorted","index=","qsl=","field=","value="])
  except getopt.GetoptError as err:
    print str(err)
    usage()
    sys.exit(2)
  dryrun = False
  sort = True
  indices = list()
  qsl_rcvd = None
  qsl_sent = None
  field = None
  value = None
  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    elif o in ("-n", "--dry-run"):
      dryrun = True
    elif o in ("-u", "--unsorted"):
      sort = False
    elif o in ("-i", "--index"):
      for x in a.split(','):
        index = x.split('-')
        for val in index:
          assert val.isdigit(), "-i must be one or more numbers or range separated by comma (,)"
        if len(index) == 1:
          indices.append(int(index[0]))
        elif len(index) == 2:
          start = int(index[0])
          finish = int(index[1]) + 1
          for x in range(start, finish):
            indices.append(int(x))
        else:
          usage()
          assert False, "wrong format of option -i"
    elif o in ("-q", "--qsl"):
      if "r" in a.lower():
        qsl_rcvd = "Y"
      if "n" in a.lower():
        qsl_rcvd = "N"
      if "s" in a.lower():
        qsl_sent = "Y"
      if "q" in a.lower():
        qsl_sent = "Q"
    elif o in ("-f", "--field"):
      field = a.lower()
    elif o in ("-v", "--value"):
      value = a
    else:
      assert False, "unhandled option"
  if len(adifs) < 1:
    usage()
    sys.exit(2)

  fieldtemplate =            "{:<4} {:8s} {:8s} {:11s} {:6s} {:5s} {:10s} {:3s} {:4s} {:4s} {:30s}"
  print fieldtemplate.format("# ID", "DATE","TIME","CALL","MODE","BAND","QRG","PWR","rQSL","sQSL","EMAIL")

  modified_logbook = False
  na = "N/A"
  c = 1
  for fn in adifs:
    logbook = parse(fn)
    if sort:
      logbook = sortlogbook(logbook)
    for qso in logbook:
      printqso = True
      if indices:
        printqso = False
        if c in indices:
          printqso = True
          if qsl_rcvd:
            qso["qsl_rcvd"] = qsl_rcvd
            modified_logbook = True
          if qsl_sent:
            qso["qsl_sent"] = qsl_sent
            modified_logbook = True
          if field and value:
            qso[field] = value
            modified_logbook = True
      if printqso:
        try:
          print fieldtemplate.format( c,
                                      qso["qso_date"] if "qso_date" in qso else na,
                                      qso["time_on"] if "time_on" in qso else na,
                                      qso["call"] if "call" in qso else na,
                                      qso["mode"] if "mode" in qso else na,
                                      qso["band"] if "band" in qso else na,
                                      qso["freq"] if "freq" in qso else na,
                                      qso["tx_pwr"] if "tx_pwr" in qso else na,
                                      qso["qsl_rcvd"] if "qsl_rcvd" in qso else "",
                                      qso["qsl_sent"] if "qsl_sent" in qso else "",
                                      qso["email"] if "email" in qso else na,
                                    )
        except IOError as e:
          if e.errno == errno.EPIPE:
            if modified_logbook and not dryrun:
              save(fn, logbook)
            sys.exit(0)
      c += 1
    if modified_logbook and not dryrun:
      save(fn, logbook)

if __name__ == '__main__':
  main()
