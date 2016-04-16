#!/usr/bin/env python
# -*- coding: utf-8 vi:noet

import io, os, sys, re, copy, subprocess, hashlib, struct, itertools
import numpy as np
import cv2

def imread(filename):

	with io.open(filename, "rb") as f:

		def eat_word():
			s = []
			while True:
				c = f.read(1)
				if c in (b"\t", b" ", b"\n"):
					return b"".join(s)
				s.append(c)

		_p6 = eat_word()
		assert _p6 == b"P6"

		c = f.read(1)
		if c in (b"#"):
			while True:
				break
		else:
			f.seek(-1, 1)

		_w = eat_word()
		w = int(_w)
		_h = eat_word()
		h = int(_h)
		_255 = eat_word()
		assert _255 == b"255"
		pos = f.tell()

	m = np.memmap(filename,
	 dtype=np.uint8,
	 mode="r",
	 offset=pos,
	 shape=(h,w,3),
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
		tpl = "<slice {0:%s}x{1:%s} ({2:%s},{3:%s},{4:%s},{5:%s}) />" \
		 % (pat, pat, pat, pat, pat, pat)
		return tpl.format(w, h, self._l, self._t, self._r, self._b)

	def size(self):
		return len(self._header) + (self._r - self._l) * (self._b - self._t) * 3

	def read(self, offset, length):

		h_pos = offset
		h_len = max(0, min(length, len(self._header) - offset))
		#print("header", h_pos, h_len)

		data_h = self._header[h_pos:h_pos+h_len]
		#print("data_h", data_h, len(data_h))

		subimg_flat = self._subimg.reshape((self._r-self._l)*(self._b-self._t)*3)
		#print("subimg_flat", subimg_flat)

		d_pos = max(offset - len(self._header), 0)
		d_len = length - h_len
		#print("d_pos", d_pos)
		#print("d_len", d_len)

		data_b = d_pos
		data_e = d_pos + d_len
		data = subimg_flat[data_b:data_e]
		#print("data", data, data_b, data_e)
		res = data_h + data.tobytes()
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
	assert len(a) == 10

	a = s.read(1, 20)
	print(b"[" + binascii.hexlify(a) + b"]")
	assert len(a) == 20

