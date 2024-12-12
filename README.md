# watch_bacula_SD-FD.py

- A script to monitor running job information from SD(s) and/or FD(s).

```
Usage: watch_bacula_SD-FD.py [-h] [-v] [-b BCONSOLE] [-c CONFIG] [-C CLIENT] [-S STORAGE] [-N] [-V] [-J] [-L] [-s]

Print out relevent running job information from SD(s) and/or FD(s)

options:
  -h, --help            show this help message and exit
  -v, --version         Print the script version
  -b BCONSOLE, --bconsole BCONSOLE
                        Path to bconsole binary [default: /opt/bacula/bin/bconsole]
  -c CONFIG, --config CONFIG
                        Path to bconsole configuration file [default: /opt/bacula/etc/bconsole.conf]
  -C CLIENT, --client CLIENT
                        Client(s) to monitor eg: -C cli1[,cli2,...]
  -S STORAGE, --storage STORAGE
                        Storage(s) to monitor eg: -S stor1[,stor2,...]
  -N, --dont_print_daemon_name
                        Don't print the daemon name in header? [default: False]
  -V, --dont_print_daemon_ver
                        Don't print the daemon version in header? [default: False]
  -J, --dont_strip_jobname
                        Don't strip the timestamp from job name? [default: False]
  -L, --print_cloud     Print the cloud status for the SD output? [default: True]
  -s, --print_spool     Print the SD's spooling information line? [default: False]
```

### Example Usage:
```
# watch -tnX watch_bacula_SD-FD.py [-C clientName] [-S storageName] [-N] [-V] [-J] [-L] [-s]

- Where X is some number of seconds between iterations
- Use -N to disable the daemon name in the headers
- Use -V to disable the daemon version in the headers
- Use -J to not strip the long timestamp from the job names displayed
- Use -L to print the cloud Upload and Download statistics for SD output
- Use -s to print the SD's spooling information line
- One or both of '-S storageName' '-C clientName' must be specified
  *NOTE: Multiple Storage and/or Client names may be specified by
         separating them with commas and no spaces like:

# watch -tnX ./watch_bacula_SD-FD.py -S stor1,stor2 -C cli1,cli2
```

### Sample command line to monitor one SD and two Clients while a job is running:
```
# watch -tn1 watch_bacula_SD-FD.py -S bacula-file -C bacula-fd,x1carbon-fd
```

Note: Since we are calling `watch_bacula_SD-FD.py` using `watch -tn1`, the output below will be dynamically updated every second:

### Sample output using the above command line:
```
========================================
Storage: bacula-file (bacula-sd v15.0.2)
========================================
Writing: Incremental Backup job Bacula JobId=69689 Volume="c0_0013_0065"
pool="Offsite-eSATA-Full" device="bacula_drv_2" (/opt/comm-bacula/vchanger/bacula-file/2)
Files=2,464 Bytes=21,912,029,080 AveBytes/sec=38,989,375 LastBytes/sec=6,792,240

=====================================
Client: bacula-fd (bacula-fd v15.0.2)
=====================================
JobId 69689 Job Bacula is running.
Incremental Backup Job started: 11-Dec-24 20:38
Files=2,464 Bytes=21,911,725,664 AveBytes/sec=35,570,983 LastBytes/sec=7,151,395 Errors=0
Bwlimit=0 ReadBytes=39,315,796,362
Files: Examined=124,482 Backed up=2,464
Processing file: /usr/lib/tmpfiles.d

===========================================================
Client: x1carbon-fd (x1carbon-fd v15.0.2) - No Jobs Running
===========================================================
```
