#########
imgtilefs
#########

Usage
#####

Assume you have a folder containing tileable pictures (eg. ppm):

.. code:: sh

   ls ~/Pic

::

   a.ppm

.. code:: sh

   file ~/Pic/a.ppm

::
   ~/Pic/a.ppm: Netpbm image data, size = 20 x 20, rawbits, pixmap


You mount it:

.. code:: sh

   imgtilefs.py ~/Pic ~/mnt/imgtilefs -o w=10,h=10

Note: options don't exist as of now.

And then:

.. code:: sh

   ls ~/mnt/imgtilefs

::

   a@000,000+010x010.ppm
   a@000,010+010x010.ppm
   a@010,000+010x010.ppm
   a@010,010+010x010.ppm

