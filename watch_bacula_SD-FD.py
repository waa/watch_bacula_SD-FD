#!/usr/bin/python3
#
# --------------------------------------------------------------------------------
# - watch_bacula_SD-FD.py - Latest version may be found at: https://github.com/waa
# --------------------------------------------------------------------------------
#
# - Bill Arlofski - Given a Client or Storage (or both) on the command line,
#                   this script will contact to the Director using bconsole,
#                   get the status(es) and print the running jobs information.
#                 - Please see included README.md for instructions and examples.
# --------------------------------------------------------------------------------
#
# BSD 2-Clause License
#
# Copyright (c) 2023-2025, William A. Arlofski waa@revpol.com
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
import argparse
import subprocess

# Set some variables
# ------------------
progname = 'watch_bacula_SD-FD'
version = '0.21'
reldate = 'October 03, 2024'
progauthor = 'Bill Arlofski'
authoremail = 'waa@revpol.com'
scriptname = 'watch_bacula_SD-FD.py'
prog_info_txt = progname + ' - v' + version + ' - ' + scriptname \
                + '\nBy: ' + progauthor + ' ' + authoremail + ' (c) ' + reldate + '\n\n'

# Set some strings to be removed from the Storage and Client status outputs
# -------------------------------------------------------------------------
remove_str_lst = [' newbsr=[01]', 'Backup Job .* waiting for.*connection.\n',
                  'Connecting to Director.*\n', 'Director connected.*$',
                  ' +FDReadSeqNo.*?\n', ' +FDSocket.*?\n', 'No Jobs running\\.$',
                  ' +SDReadSeqNo=.*?\n', ' +SDSocket.*?\n']

# Create the storage and client list place holders
# ------------------------------------------------
storage_lst = client_lst = []

# Define the argparse arguments, descriptions, defaults, etc
# waa - Something to look into: https://www.reddit.com/r/Python/comments/11hqsbv/i_am_sick_of_writing_argparse_boilerplate_code_so/
# ---------------------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(prog=scriptname, description='Print out relevent running job information from SD(s) and/or FD(s)')
parser.add_argument('-v', '--version', help='Print the script version', version=scriptname + " v" + version, action='version')
parser.add_argument('-b', '--bconsole', help='Path to bconsole binary [default: /opt/bacula/bin/bconsole]', default='/opt/bacula/bin/bconsole', type=argparse.FileType('r'))
parser.add_argument('-c', '--config', help='Path to bconsole configuration file [default: /opt/bacula/etc/bconsole.conf]', default='/opt/bacula/etc/bconsole.conf', type=argparse.FileType('r'))
parser.add_argument('-C', '--client', help='Client(s) to monitor eg:  -C cli1[,cli2,...]')
parser.add_argument('-S', '--storage', help='Storage(s) to monitor eg:  -S stor1[,stor2,...]')
parser.add_argument('-N', '--dont_print_daemon_name', help='Don\'t print the daemon name in header? [default: False]', action='store_true')
parser.add_argument('-V', '--dont_print_daemon_ver', help='Don\'t print the daemon version in header? [default: False]', action='store_true')
parser.add_argument('-J', '--dont_strip_jobname', help='Don\'t strip the timestamp from job name? [default: False]', action='store_true')
parser.add_argument('-L', '--print_cloud', help='Print the cloud status for the SD output? [default: True]', action='store_true')
parser.add_argument('-s', '--print_spool', help='Print the SD\'s spooling information line? [default: False]', action='store_true')
args = parser.parse_args()

# Now for some functions
# ----------------------
def usage():
    'Show the instructions and program information.'
    parser.print_help()
    print('\n' + prog_info_txt)
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
    match = re.match(r'.*\n(.*?) Version: (\d+\.\d+\.\d+) .*', fs, flags = re.S)
    if match:
        ver = match[2]
        daemon = match[1]
    else:
        ver = 'N/A'
        daemon = 'N/A'
    return ver, daemon

def get_and_clean_output(cl):
    'If passed True (ie: get_and_clean_output(True), build and output Client-specific block, else Storage-specific block.'
    cloud_status = ''
    cmd_str = 'echo -e "status ' + ('client=' + client if cl else 'storage=' + storage) + '\nquit\n"'
    cmd = cmd_str + ' | ' + bconsole + ' -c ' + config
    full_status = get_shell_result(cmd).stdout
    if print_daemon_ver or print_daemon_name:
        version, daemon = get_version_and_daemon(full_status)
    running_status = running_jobs(full_status)
    # Try to get the cloud transfer status if we are contacting an SD
    # ---------------------------------------------------------------
    if not cl:
        if print_cloud_stats:
            cloud_status = cloud_xfers(full_status)
            cloud_status = re.sub(' +(Uploads)', '\n\\1:', cloud_status)
            cloud_status = re.sub(' +(Downloads)', '\\1:', cloud_status)
        # Do we print the spooling information for an SD?
        # -----------------------------------------------
        if not print_spool_line:
            running_status = re.sub('    spooling=.+?\n', '', running_status, flags = re.S)
    for remove_str in remove_str_lst:
        running_status = re.sub(remove_str, '', running_status, flags = re.S)
    running_status = re.sub('(JobId |Reading: |Writing: )', '\n\\1', running_status, flags = re.S)
    if strip_jobname:
        running_status = re.sub(r'\.[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}\.[0-9]{2}\.[0-9}{2}_[0-9].*? ', ' ', running_status)
    header_str = '\n' + ('Client: ' + client if cl else 'Storage: ' + storage) \
               + (' (' if print_daemon_ver or print_daemon_name else '') \
               + (daemon if print_daemon_name else '') \
               + (' ' if print_daemon_name and print_daemon_ver else '') \
               + ('v' + version if print_daemon_ver else '') \
               + (')' if print_daemon_ver or print_daemon_name else '') \
               + (' - No Jobs Running' if len(running_status) == 0 else '') \
               + '\n'
    line = '='*(len(header_str) - 2)
    return (line + header_str + line \
          + ('\n' if len(running_status) == 0 else '') \
          + (running_status if len(running_status) > 0 else '') \
          + (cloud_status + '\n' if not cl and (len(cloud_status) > 0 and len(running_status) > 0) else ''))

# ================
# BEGIN the script
# ================
# Assign variables from args set
# ------------------------------
bconsole = args.bconsole.name
config = args.config.name
print_cloud_stats = args.print_cloud
print_spool_line = args.print_spool
print_daemon_ver = not args.dont_print_daemon_ver
print_daemon_name = not args.dont_print_daemon_name
strip_jobname = not args.dont_strip_jobname
if args.storage is None and args.client is None:
    print(print_opt_errors('sd_fd'))
    usage()
else:
    if args.storage is not None:
        storage_lst = [s for s in args.storage.split(',')]
    if args.client is not None:
        client_lst = [c for c in args.client.split(',')]

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

# Call get_and_clean_output() for Storage(s), or Client(s), or both
# -----------------------------------------------------------------
output = ''
for storage in storage_lst:
    output += ('\n' if storage_lst.index(storage) != 0 else '') + get_and_clean_output(False)
for client in client_lst:
    output += ('\n' if client_lst.index(client) != 0 or len(storage_lst) !=0 else '') + get_and_clean_output(True)
print(output)
