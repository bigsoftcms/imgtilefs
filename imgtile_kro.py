#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# Provide a PPM buffer interface in a Kolor .kro image

import io, os, sys, re, copy, subprocess, hashlib, struct, itertools
import numpy as np
import cv2

def imread(filename):

	with open(filename, "rb") as f:
		kro, w, h, dep, ncomp = struct.unpack(">4sIIII", f.read(20))

	m = np.memmap(filename,
	 dtype=np.uint8,
	 mode="r",
	 offset=20,
	 shape=(h,w,4),
	)
	return m


class ImageSlice(object):
	def __init__(self, img, t, l, b, r):
		self._img = img
		self._t = t
		self._l = l
		self._b = b
		self._r = r
		self._subimg = img[t:b,l:r]
		self._header = ("P6\t%s %s\t255\n" % (r-l, b-t)).encode("utf-8")

	def __str__(self):
		h, w = self._img.shape[:2]
		zeros = max(len(str(h)), len(str(w)))
		pat = "%dd" % zeros
		tpl = "<slice_kro {0:%s}x{1:%s} ({2:%s},{3:%s},{4:%s},{5:%s}) />" \
		 % (pat, pat, pat, pat, pat, pat)
		return tpl.format(w, h, self._l, self._t, self._r, self._b)

	def size(self):
		return len(self._header) + (self._r - self._l) * (self._b - self._t) * 3

	def read(self, offset, length):
		"""
		Read RGB from an RGBA buffer

		Find the buffer containing at leas the data to be extracted,
		then split/merge it, then seek inside.
		"""
		#print("read from %d for %d" % (offset, length))
		h_pos = offset
		h_len = max(0, min(length, len(self._header) - offset))
		#print("header", h_pos, h_len)

		data_h = self._header[h_pos:h_pos+h_len]
		#print("data_h", data_h, len(data_h))

		subimg_flat = self._subimg.reshape(((self._r-self._l)*(self._b-self._t), 1, 4))
		
		# position inside the body in output space
		b_pos = (max(offset - len(self._header), 0))
		b_len = (length - h_len)
		#print("b_pos", b_pos)
		#print("b_len", b_len)

		# position inside the body in input buffer
		d_pos = (b_pos) // 3
		d_len = (b_len + 4) // 3
		#print("d_pos", d_pos)
		#print("d_len", d_len)

		o = b_pos - d_pos * 3

		if d_len == 0:
			data_b = b""
		else:
			data = subimg_flat[d_pos:d_pos+d_len]
			#print("data", data, data_b, data_e)
			r, g, b, a = cv2.split(data)
			buf = cv2.merge((r, g, b))
			#print("buf", buf.shape, buf)
			buf_flat = buf.reshape(buf.shape[0] * buf.shape[2])
			#print("buf_flat", buf_flat)
			data_b = buf_flat[o:o+b_len].tobytes()

		res = data_h + data_b
		#print("res", res, len(res))
		return res

class ImageTiler(object):
	def __init__(self, img, tile_w, tile_h):
		self.tiles = []
		pass


if __name__ == '__main__':

	import binascii

	img = imread(sys.argv[1])
	print(img.shape)

	s = ImageSlice(img, 10, 10, 20, 20)
	
	a = s.read(0, 0)
	assert len(a) == 0

	a = s.read(20, 0)
	assert len(a) == 0
	
	a = s.read(0, 10)
	assert len(a) == 10


	a = s.read(0, 10)
	print(b"[" + a + b"]")
	assert len(a) == 10, len(a)

	a = s.read(1, 20)
	print(b"[" + binascii.hexlify(a) + b"]")
	assert len(a) == 20, len(a)

