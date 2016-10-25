nRF24LE1 Programmer
================

This software is used to write the flash memory of nRF24LE1 chips. It can handle a standard Intel HEX file which is the output of e.g. Keil.

Currently this software just support the Orange Pi Allwinner H3 plattform. But a migration to a other plattform like a Raspberry Pi should be an easy Task. The only plattform specific is the GPIO handling.

Usage
=================

`python nrf24le1.py "pathtohex"`

Wiring
=================

PA13 - FPROG

PA14 - FRESET

PD14 - FCSN

MISO - FMISO

MOSI - FMOSI

SCK - FSCK
