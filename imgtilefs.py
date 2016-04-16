#!/usr/bin/env python
# -*- coding: utf-8 vi:noet

import io, os, sys, re, copy, subprocess, hashlib, struct, itertools, argparse

from errno import EACCES
from threading import Lock

import numpy as np
import cv2

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

import imgtile_ppm
import imgtile_kro

class ImageTileFS(LoggingMixIn, Operations):	
	def __init__(self, root):
		self.log.info("pouet")
		self.root = os.path.realpath(root)
		self.map = dict() # filename vs. map of tile names vs. tiles
		self._v2r = dict()
	
	def __call__(self, op, path, *args):
		return super(ImageTileFS, self).__call__(op, self.root + path, *args)
	
	def access(self, path, mode):
		#print("access %s %s" % (path, mode))
		if path in self._v2r:
			pass
			#if not os.access(path, mode):
			#raise FuseOSError(EACCES)
	
	chmod = os.chmod
	chown = os.chown
	
	def create(self, path, mode):
		return os.open(path, os.O_WRONLY | os.O_CREAT, mode)
	
	def flush(self, path, fh):
		return os.fsync(fh)

	def fsync(self, path, datasync, fh):
		return os.fsync(fh)
	
	def getattr(self, path, fh=None):
		#print("getattr %s" % path)
		res = dict()
		if os.path.isdir(path):
			#print("dir")
			st = os.lstat(path)
			res = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
				'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
		elif path in self._v2r:
			org = self._v2r[path]
			#print("v2r of %s" % org)
			name = os.path.basename(path)
			st = os.lstat(org)
			res = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
				'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
			res['st_size'] = self.map[org][name].size()
			res['st_mode'] = 0o0100000 | 0o444
			#res['st_mtime'] -= 1.0
		else:
			#print("other")
			st = os.lstat(path)
			res = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
				'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
		#print(res)
		#print(oct(res['st_mode']))
		return res
	
	getxattr = None
	
	def link(self, target, source):
		return os.link(source, target)
	
	listxattr = None
	mkdir = os.mkdir
	mknod = os.mknod

	def open(self, path, flag, mode=int("0777", 8)):
		#print("open %s" % path)
		if path in self._v2r:
			org = self._v2r[path]
			name = os.path.basename(path)
			s = self.map[org][name]
			return os.open(org, flag, mode)
		else:
			#print("cannot open")
			raise NotImplementedError()
	
	def read(self, path, size, offset, fh):
		#print("read %s %d %d" % (path, offset, size))
		if path in self._v2r:
			org = self._v2r[path]
			name = os.path.basename(path)
			s = self.map[org][name]
			return s.read(offset, size)
		else:
			#print("cannot read")
			raise NotImplementedError()
		
	def readdir(self, path, fh):
		#print("readdir %s %s" % (path, fh))
		files2 = []
		files = os.listdir(path)
		for fn in files:
			if fn.endswith(".ppm") or fn.endswith(".kro"):
				files2 += self.build(path, fn)
		return ['.', '..'] + files2

	readlink = os.readlink
	
	def release(self, path, fh):
		#print("release %s" % path)
		return os.close(fh)
		
	def rename(self, old, new):
		return os.rename(old, self.root + new)
	
	rmdir = os.rmdir
	
	def statfs(self, path):
		stv = os.statvfs(path)
		return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
			'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
			'f_frsize', 'f_namemax'))
	
	def symlink(self, target, source):
		return os.symlink(source, target)
	
	def truncate(self, path, length, fh=None):
		with open(path, 'r+') as f:
			f.truncate(length)
	
	unlink = os.unlink
	utimens = os.utime
	
	def write(self, path, data, offset, fh):
		raise NotImplementedError()

	def build(self, dirname, basename):
		path = os.path.join(dirname, basename)
		if path not in self.map:
			if basename.endswith(".ppm"):
				img = imgtile_ppm.imread(path)
				tw = 1024
				th = 1024
				h, w = img.shape[:2]
				nb_x = w//tw
				nb_y = h//th
				subimages = dict()
				for idx_y in range(nb_y):
					for idx_x in range(nb_x):
						ih = min(th, h - idx_y * th)
						iw = min(tw, w - idx_x * tw)
						name = "%s@%05dx%05d+%05d+%05d.ppm" \
						 % (basename[:-4], iw, ih, idx_y * th, idx_x * tw)
						subimages[name] = imgtile_ppm.ImageSlice(
						 img,
						 idx_y * th,
						 idx_x * tw,
						 idx_y * th + ih,
						 idx_x * tw + iw,
						)
						subpath = os.path.join(dirname, name)
						self._v2r[subpath] = path
				self.map[path] = subimages
			elif basename.endswith(".kro"):
				img = imgtile_kro.imread(path)
				tw = 1024
				th = 1024
				h, w = img.shape[:2]
				nb_x = w//tw
				nb_y = h//th
				subimages = dict()
				for idx_y in range(nb_y):
					for idx_x in range(nb_x):
						ih = min(th, h - idx_y * th)
						iw = min(tw, w - idx_x * tw)
						name = "%s@%05dx%05d+%05d+%05d.ppm" \
						 % (basename[:-4], iw, ih, idx_y * th, idx_x * tw)
						subimages[name] = imgtile_kro.ImageSlice(
						 img,
						 idx_y * th,
						 idx_x * tw,
						 idx_y * th + ih,
						 idx_x * tw + iw,
						)
						subpath = os.path.join(dirname, name)
						self._v2r[subpath] = path
				self.map[path] = subimages
			else:
				self.map[path] = dict()
		for k, v in sorted(self.map[path].items()):
			print(" - %s: %s" % (k, v))
		return sorted(self.map[path].keys())

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	
	parser.add_argument(
	 "--verbose",
	 action="store_true",
	 dest="verbose",
	 default=False,
	 help="verbose output, and prompts for exit",
	)
	parser.add_argument("root")
	parser.add_argument("mountpoint")
	
	args = parser.parse_args()
	verbose = args.verbose

	kw = {}
	if verbose:
		kw['foreground'] = True
	
	fuse = FUSE(ImageTileFS(args.root), args.mountpoint, **kw)

