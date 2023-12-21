#!/usr/bin/python3
#
# ---------------------------------------------------------------------------
# - watch_bacula_SD-FD.py
# ---------------------------------------------------------------------------
#
# - Bill Arlofski - Given a Storage or Client (or both) on the command line,
#                   this script will contact the Director using bconsole, get
#                   the status(es) and print the running jobs information.
#                 - For best results this script should be called using the
#                   Linux `watch` utility like:
#
# watch -tn X ./watch_bacula_SD-FD.py [-S storageName] [-C clientName]
#
# - Where X is some number of seconds between iterations
# - Use '-V no' to disable the daemon version in the headers
# - Use '-N no' to disable the daemon name in the headers
# - One or both of '-S storageName' '-C clientName' must be specified
#   *NOTE: Multiple Storage and/or Client names may be specified by
#          separating them with commas and no spaces like:
#
#          watch -tn X ./watch_bacula_SD-FD.py -S stor1,stor2 -C cli1,cli2
# 
# The latest version of this script may be found at: https://github.com/waa
#
# ---------------------------------------------------------------------------
#
# BSD 2-Clause License
#
# Copyright (c) 2023, William A. Arlofski waa@revpol.com
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1.  Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2.  Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ---------------------------------------------------------------------------
#
# ==================================================
# Nothing below this line should need to be modified
# ==================================================
#
# Import the required modules
# ---------------------------
import os
import re
import sys
import subprocess
from docopt import docopt

# Set some variables
# ------------------
progname = 'watch_bacula_SD-FD'
version = '0.12'
reldate = 'December 21, 2023'
progauthor = 'Bill Arlofski'
authoremail = 'waa@revpol.com'
scriptname = sys.argv[0]
prog_info_txt = progname + ' - v' + version + ' - ' + scriptname \
                + '\nBy: ' + progauthor + ' ' + authoremail + ' (c) ' + reldate + '\n\n'

# Set some strings to be removed from the Storage and Client status outputs
# -------------------------------------------------------------------------
remove_str_lst = ['Backup Job .* waiting for.*connection.\n',
                  'Connecting to Director.*\n', 'Director connected.*$',
                  ' +FDReadSeqNo.*?\n', ' +FDSocket.*?\n', 'No Jobs running\.$',
                  ' +SDReadSeqNo=.*?\n', ' +SDSocket.*?\n']

# Create the storage and client place holder lists
# ------------------------------------------------
storage_lst = client_lst = []

# Define the docopt string
# ------------------------
doc_opt_str = """
Usage:
    watch_bacula_SD-FD.py [-b <bconsole>] [-c <config>] [-S <storage>] [-C <client>] [-V] [-N] [-D]
    watch_bacula_SD-FD.py -h | --help
    watch_bacula_SD-FD.py -v | --version

Options:
    -b, --bconsole <bconsole>        Path to bconsole [default: /opt/comm-bacula/sbin/bconsole]
    -c, --config <config>            Configuration file [default: /opt/comm-bacula/etc/bconsole.conf]
    -S, --storage <storage>          Storage to monitor
    -C, --client <client>            Client to monitor
    -N, --dont_print_daemon_name     Do we print the daemon name in header?
    -V, --dont_print_daemon_ver      Do we print the daemon version in header?
    -D, --dont_print_cloud           Do we print the cloud stats for the SD output?

    -h, --help                       Print this help message
    -v, --version                    Print the script name and version

Notes:
  * A valid storage or a client, or both, must be specified

"""

# Now for some functions
# ----------------------
def usage():
    'Show the instructions and program information.'
    print(doc_opt_str)
    print(prog_info_txt)
    sys.exit(1)

def print_opt_errors(opt):
    'Print the incorrect variable and the reason it is incorrect.'
    if opt == 'sd_fd':
        error_txt = 'Both Storage and Client were not specified. One or both are required.'
    elif opt == 'bin':
        error_txt = 'The \'bconsole\' variable, pointing to \'' + bconsole + '\' does not exist or is not executable.'
    elif opt == 'config':
        error_txt = 'The config file \'' + config + '\' does not exist or is not readable.'
    return '\n' + error_txt

def get_shell_result(cmd):
    'Given a command to run, return the subprocess.run() result object.'
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def running_jobs(fs):
    'Given a full_status output, use re.sub() to grab the "Running Jobs:" section from the full_status output.'
    return re.sub('.*Running Jobs:\n(.+?)\n====.*', '\\1', fs, flags = re.S)

def cloud_xfers(fs):
    'Given a full_status output, use re.sub() to grab the "Cloud transfer status:" section from the full_status output.'
    if 'Cloud transfer status' in fs:
        return re.sub('.*Cloud transfer status:.*?\n(.+?)\n====.*', '\\1', fs, flags = re.S)
    else:
        return ''

def get_version_and_daemon(fs):
    'Use re.match() to grab the Bacula SD/FD version from the full_status output.'
    match = re.match('.*\n(.*?) Version: (\d+\.\d+\.\d+) .*', fs, flags = re.S)
    if match:
        ver = match[2]
        daemon = match[1]
    else:
        ver = 'N/A'
        daemon = 'N/A'
    return ver, daemon

def get_clean_and_print_output(cl):
    'Passed True (ie: client=True), build and output Client-specific block, else Storage-specific block.'
    cmd_str = 'echo -e "status ' + ('client=' + client if cl else 'storage=' + storage) + '\nquit\n"'
    cmd = cmd_str + ' | ' + bconsole + ' -c ' + config
    full_status = get_shell_result(cmd).stdout
    if print_daemon_ver or print_daemon_name:
        version, daemon = get_version_and_daemon(full_status)
    else:
        daemon = version = ''
    running_status = running_jobs(full_status)
    # Try to get the cloud transfer status if we are contacting an SD
    # ---------------------------------------------------------------
    if not cl and print_cloud_stats:
        cloud_status = cloud_xfers(full_status)
        cloud_status = re.sub(' +(Uploads)', '\n\\1:', cloud_status)
        cloud_status = re.sub(' +(Downloads)', '\\1:', cloud_status)
    else:
        cloud_status = ''
    for remove_str in remove_str_lst:
        running_status = re.sub(remove_str, '', running_status, flags = re.S)
    running_status = re.sub('(JobId |Reading: |Writing: )', '\n\\1', running_status, flags = re.S)
    header_str = '\n' + ('Client: ' + client if cl else 'Storage: ' + storage) \
               + (' (' if print_daemon_ver or print_daemon_name else '') \
               + (daemon if print_daemon_name else '') \
               + (' ' if print_daemon_name and print_daemon_ver else '') \
               + ('v' + version if print_daemon_ver else '') \
               + (')' if print_daemon_ver or print_daemon_name else '') \
               + (' - No Jobs Running' if len(running_status) == 0 else '') \
               + '\n'
    line = '='*(int(len(header_str)) - 2)
    print(line + header_str + line \
          + ('\n' if len(running_status) == 0 else '') \
          + (running_status if len(running_status) > 0 else '') \
          + (cloud_status + '\n' if (len(cloud_status) > 0 and len(running_status) > 0) else ''))

# ================
# BEGIN the script
# ================
# Assign docopt doc string variable
# ---------------------------------
args = docopt(doc_opt_str, version='\n' + progname + ' - v' + version + '\n' + reldate + '\n')

# Assign variables from args set
# ------------------------------
bconsole = args['--bconsole']
config = args['--config']
print_daemon_ver = not args['--dont_print_daemon_ver']
print_daemon_name = not args['--dont_print_daemon_name']
print_cloud_stats = not args['--dont_print_cloud']
if args['--storage'] is None and args['--client'] is None:
    print(print_opt_errors('sd_fd'))
    usage()
else:
    if args['--storage'] is not None:
        storage_lst = [s for s in args['--storage'].split(',')]
    if args['--client'] is not None:
        client_lst = [c for c in args['--client'].split(',')]

# Check that the bconsole binary exists and is executable
# -------------------------------------------------------
if not os.path.exists(bconsole) or not os.access(bconsole, os.X_OK):
    print(print_opt_errors('bin'))
    usage()

# Check that the bconsole config file exists and is readable
# ----------------------------------------------------------
if not os.path.exists(config) or not os.access(config, os.R_OK):
    print(print_opt_errors('config'))
    usage()

# Call get_clean_and_print_output() for Storage, or Client, or both
# -----------------------------------------------------------------
if storage_lst is not None:
    for storage in storage_lst:
        get_clean_and_print_output(False)
if client_lst is not None:
    for client in client_lst:
        get_clean_and_print_output(True)
