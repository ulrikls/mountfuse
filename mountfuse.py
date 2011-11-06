#!/usr/bin/env python -tt
# -*- coding: UTF-8 -*-
"""
Created on Sat Nov  5 21:11:00 2011

@author: Ulrik Landberg Stephansen <ulrikls@papio.dk>
"""

import sys
from optparse import OptionParser
from urlparse import urlparse
import subprocess
import re
import os

def main():
  """Main function."""

  # Define options
  parser = OptionParser(usage = u'mountfuse [options] URL', description = u'Interface for FUSE network file systems (currently SSH and FTP). Run with no arguments to list current FUSE mounts.')
  parser.add_option(u'-d', u'--mountpoint', dest = u'mountpoint', help = u'mountpoint (empty directory)', type = u'string')
  parser.add_option(u'-n', u'--volname', dest = u'volname', help = u'volume display name', type = u'string')
  parser.add_option(u'-u', dest = u'unmountnumber', help = u'unmount mount number', type = u'int')
  parser.add_option(u'--unmount', dest = u'unmountpoint', help = u'unmount specified mountpoint', type = u'string')

  # Parse options and arguments
  (options, args) = parser.parse_args()
  if options.unmountpoint:
    dounmount(options.unmountpoint)
  elif options.unmountnumber:
    mounts = listmounts()
    if len(mounts) < options.unmountnumber:
      sys.stderr.write(u'No mount number %d.' % options.unmountnumber)
      printmounts(mounts)
      return 1
    dounmount(mounts[options.unmountnumber - 1][2])
  elif len(args) < 1:
    mounts = listmounts()
    printmounts(mounts)
    return 0
  else:
    return domount(args[-1], options.mountpoint, options.volname)




def listmounts():
  """List filesystems currently mounted."""
  mounts = subprocess.Popen(u'mount', stdout=subprocess.PIPE).communicate()[0]
  mounts = re.findall(r'([\w.]*?):(.*?) on (.*?) .*?fuse4x.*?', mounts, re.IGNORECASE)
  return mounts




def printmounts(mounts):
  """Print filesystems currently mounted."""
  print u'Current FUSE mounts:'
  if mounts:
    number = 0
    for mount in mounts:
      (host, path, mountpoint) = mount
      number += 1
      print u'%3d) %s:%s on %s' % (number, host, path, mountpoint)
  else:
    print u'None'




def domount(url, mountpoint=None, volname=None):
  """Mount filesystem based on url scheme."""
  url = urlparse(url)

  if url.scheme == u'ssh' or url.scheme == u'sftp':
    return domountssh(url, mountpoint, volname)
  elif url.scheme == u'ftp':
    return domountftp(url, mountpoint, volname)
  else:
    sys.stderr.write(u'URL scheme "%s" not supported.\n' % url.scheme)
    return 1





def domountssh(url, mountpoint=None, volname=None):
  """Mount SSHFS filesystem."""
  icon = u'sshfs.icns'

  # Get mountpoint
  mountgenerated = False
  if not mountpoint:
    mountpoint = makemountpoint()
    mountgenerated = True

  # Get volume name
  if not volname:
    volname = u'SSH %s%s' % (url.hostname, url.path)

  # Mount
  if url.netloc[-1] == u':':
    command = [u'sshfs', u'%s%s' % (url.netloc, url.path), mountpoint]
  else:
    command = [u'sshfs', u'%s:%s' % (url.netloc, url.path), mountpoint]
  if url.port:
    command += [u'-p', url.port]
  command += [u'-o', u'follow_symlinks']
  command += [u'-o', u'auto_cache']
  if os.path.exists(icon):
    command += [u'-o', u'volicon=%s' % icon]
  command += [u'-o', u'volname=%s' % volname]

  if subprocess.call(command) > 0:
    sys.stderr.write(u'Could not mount "%s".\n' % url.geturl())
    if mountgenerated and os.path.exists(mountpoint):
      os.rmdir(mountpoint)
    return 1

  print u'%s mounted on %s' % (url.geturl(), mountpoint)
  return 0




def domountftp(url, mountpoint=None, volname=None):
  """Mount FTPFS filesystem."""
  icon = u''

  # Get mountpoint
  mountgenerated = False
  if not mountpoint:
    mountpoint = makemountpoint()
    mountgenerated = True

  # Get volume name
  if not volname:
    volname = u'FTP %s%s' % (url.hostname, url.path)

  # Mount
  command = [u'curlftpfs', url.geturl(), mountpoint]
  if url.username:
    command += [u'-o', u'user=%s' % url.username]
  command += [u'-o', u'auto_cache']
  if os.path.exists(icon):
    command += [u'-o', u'volicon=%s' % icon]
  command += [u'-o', u'volname=%s' % volname]

  if subprocess.call(command) > 0:
    sys.stderr.write(u'Could not mount "%s".\n' % url.geturl())
    if mountgenerated and os.path.exists(mountpoint):
      os.rmdir(mountpoint)
    return 1

  print u'%s mounted on %s' % (url.geturl(), mountpoint)
  return 0




def makemountpoint():
  """Create new mountpoint"""
  # Get mountpoint
  mounts = listmounts()
  number = len(mounts)
  exists = True
  while exists:
    number += 1
    mountpoint = u'/Volumes/fuse%d' % (number)
    exists = os.path.exists(mountpoint)

  # Create mountpoint
  os.mkdir(mountpoint)

  return mountpoint




def dounmount(mountpoint):
  """Unmount filesystem at specified path."""
  if not os.path.exists(mountpoint):
    sys.stderr.write(u'Mountpoint "%s" does not exist.\n' % mountpoint)
    return 1
  return subprocess.call([u'diskutil', u'unmount', mountpoint])




if __name__ == u'__main__':
  main()
