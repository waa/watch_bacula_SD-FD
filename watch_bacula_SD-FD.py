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
# - And '-S storageName' and/or '-C clientName' must be specified
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
import shutil
import subprocess
from docopt import docopt

# Set some variables
# ------------------
progname = 'watch_bacula_SD-FD'
version = '0.05'
reldate = 'December 10, 2023'
progauthor = 'Bill Arlofski'
authoremail = 'waa@revpol.com'
scriptname = sys.argv[0]
prog_info_txt = progname + ' - v' + version + ' - ' + scriptname \
                + '\nBy: ' + progauthor + ' ' + authoremail + ' (c) ' + reldate + '\n\n'

# Set some strings to be removed from the Storage and Client status outputs
# -------------------------------------------------------------------------
st_remove_str_lst = ['Connecting to Director.*\n', 'Director connected.*$',
                     ' +FDReadSeqNo.*?\n', ' +FDSocket.*?\n', 'No Jobs running\.$',
                     ' +SDReadSeqNo=.*?\n', ' +SDSocket.*?\n']

# Define the docopt string
# ------------------------
doc_opt_str = """
Usage:
    watch_bacula_SD-FD.py [-b <bconsole>] [-c <config>] [-S <storage>] [-C <client>]
                          [-V <daemon_ver>] [-N <daemon_name>]
    watch_bacula_SD-FD.py -h | --help
    watch_bacula_SD-FD.py -v | --version

Options:
    -b, --bconsole <bconsole>        Path to bconsole [default: /opt/bacula/bin/bconsole]
    -c, --config <config>            Configuration file [default: /opt/bacula/etc/bconsole.conf]
    -S, --storage <storage>          Storage to monitor
    -C, --client <client>            Client to monitor
    -V, --daemon_ver <daemon_ver>    Do we print the daemon version in header? [default: yes]
    -N, --daemon_name <daemon_name>  Do we print the daemon name in header? [default: yes]

    -h, --help                       Print this help message
    -v, --version                    Print the script name and version

Notes:
  * A valid storage or a client, or both must be specified

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
    'Use re.sub() to grab the "Running Jobs:" section from the full_status output.'
    return re.sub('.*Running Jobs:\n(.+?)\n====.*', '\\1', fs, flags = re.S)

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
    cmd_str = 'echo -e "status ' + ('client=' if cl else 'storage=') \
            + (client if cl else storage) + ' running\nquit\n"'
    cmd = cmd_str + ' | ' + bconsole + ' -c ' + config 
    full_status = get_shell_result(cmd).stdout
    if print_daemon_ver or print_daemon_name:
        version, daemon = get_version_and_daemon(full_status)
    else:
        daemon = version = ''
    status = running_jobs(full_status)
    for remove_str in st_remove_str_lst:
        status = re.sub(remove_str, '', status, flags = re.S)
    status = re.sub('(JobId |Writing: )', '\n\\1', status, flags = re.S)
    header_str = '\n' + ('Client: ' if cl else 'Storage: ') \
               + (client if cl else storage) \
               + (' (' if print_daemon_ver or print_daemon_name else '') \
               + (daemon if print_daemon_name else '') \
               + (' ' if print_daemon_name and print_daemon_ver else '') \
               + ('v' + version if print_daemon_ver else '') \
               + (')' if print_daemon_ver or print_daemon_name else '') \
               + (' - No Jobs Running' if len(status) == 0 else '') \
               + '\n'
    line = '='*(int(len(header_str)) - 2)
    print(line + header_str + line + (status if len(status) > 0 else ''))

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
if args['--daemon_ver'].lower() == 'yes':
    print_daemon_ver = True
else:
    print_daemon_ver = False
if args['--daemon_name'].lower() == 'yes':
    print_daemon_name = True
else:
    print_daemon_name = False
if args['--storage'] is None and args['--client'] is None:
    print(print_opt_errors('sd_fd'))
    usage()
else:
    storage = args['--storage']
    client = args['--client']

# Check that the bconsole binary exists and is executable
# -------------------------------------------------------
if shutil.which(bconsole) is None:
    print(print_opt_errors('bin'))
    usage()

# Check that the bconsole config file exists and is readable
# ----------------------------------------------------------
if not os.path.exists(config) or not os.access(config, os.R_OK):
    print(print_opt_errors('config'))
    usage()

# Call get_clean_and_print_output() for Storage, or Client, or both
# -----------------------------------------------------------------
if storage is not None:
    get_clean_and_print_output(False)
if client is not None:
    get_clean_and_print_output(True)
