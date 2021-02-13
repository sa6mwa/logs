# sa6mwa-logs
SA6MWA Amateur Radio Operator Logs.

I have stopped using online logbook services since 2019. This is where I keep
my public QSO logs and those of other stations/callsigns that I'm activating.
Previous logs are available on my [qrz.com page](https://www.qrz.com/DB/SA6MWA).

Most files are [ADIF logs](http://www.adif.org) unless a contest/activity
requires a different logging format. I have chosen to separate the logs in
different files per activity or session. For the ADIF logs you can run
`adifaggregator.py` to generate a complete list of my QSOs in a single ADIF.

## termlog.adif

The main log is `termlog.adif`. 

## Logging software

I primarily use [termlog](https://github.com/tzneal/ham-go) which is a terminal
logger written in Golang. It supports rig control through hamlib and
experimental support for logging from wsjtx and fldigi/fllog.
