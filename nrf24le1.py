import os
import sys
import spidev

from time import sleep
from pyA20.gpio import gpio
from pyA20.gpio import port

# SPI commands
WREN = 0x06
WRDIS = 0x04
RDSR = 0x05
WRSR = 0x01
READ = 0x03
PROGRAM = 0x02
ERASE_PAGE = 0x52
ERASE_ALL = 0x62
RDFOCR = 0x89
RDISMB = 0x85
ENDEBUG = 0x86

# Bit definitions for register fsr
FSR_ENDEBUG = (1<<7)
FSR_STP = (1<<6)
FSR_WEN = (1<<5)
FSR_RDYN = (1<<4)
FSR_INFEN = (1<<3)
FSR_RDISMB = (1<<2)

# Port definition on Allwinner H3
FPROG = port.PA13
FRESET = port.PA14
FCSN = port.PD14

spi = spidev.SpiDev()

def init():
    spi.open(0, 0)
    spi.max_speed_hz = 4000000

    gpio.init()
    gpio.setcfg(FPROG, gpio.OUTPUT)
    gpio.setcfg(FRESET, gpio.OUTPUT)
    gpio.setcfg(FCSN, gpio.OUTPUT)

    gpio.output(FPROG, 0)
    gpio.output(FRESET, 1)
    gpio.output(FCSN, 1)
    return

def enter_progmode():
    # Ensure FRESET is inactive -> Datasheet p.77
    gpio.output(FRESET, 1)
    gpio.output(FPROG, 1)
    gpio.output(FRESET, 0)
    sleep(0.01)
    gpio.output(FRESET, 1)
    sleep(0.1)
    return

def exit_progmode():
    # Ensure FRESET is inactive -> Datasheet p.77
    gpio.output(FRESET, 1)
    gpio.output(FPROG, 0)
    gpio.output(FRESET, 0)
    sleep(0.01)
    gpio.output(FRESET, 1)
    sleep(0.1)
    return

def write_spi(data):
    gpio.output(FCSN, 0)
    spi.writebytes(data)
    gpio.output(FCSN, 1)

def read_spi(command, bytes):
    gpio.output(FCSN, 0)
    spi.writebytes(command)
    reply = spi.readbytes(bytes)
    gpio.output(FCSN, 1)
    return reply

def read_fsr():
    return read_spi([RDSR], 1)[0]

def write_fsr(data):
    wait_ready()
    write_spi([WRSR, data])

def wait_ready():
    while (read_fsr() & FSR_RDYN):
     #print("Flash not ready \r")
     sleep(0.1)

def set_wren():
    write_spi([WREN])
    wait_ready()
    return

def set_infen(status):
    readback = read_fsr()
    if (status):
        write_fsr(readback | FSR_INFEN)
        readback = read_fsr()
        if not (readback & FSR_INFEN):
            print("Failed to set INFEN \n")
    else:
        write_fsr(readback & ~FSR_INFEN)
        readback = read_fsr()
        if (readback & FSR_INFEN):
            print("Failed to reset INFEN \n")

def erase_all_flash_pages():
    set_infen(0)
    set_wren()
    write_spi([ERASE_ALL])
    wait_ready()
    return

def read_flash(address, length):
    return read_spi([READ, (address & 0xFF00)>>8, address & 0x00FF], length)

def write_flash(address, data):
    set_wren()
    list = [PROGRAM, (address & 0xFF00)>>8, address & 0x00FF]
    write_spi(list + data)
    print("Writing " + str(len(data)) + "Bytes to the Addrss " + hex(address))
    wait_ready()

    if not (cmp(data, read_flash(address, len(data)))):
        print("Successfill written " + hex(address) + "!")
    else:
        print("Failed with " + hex(address) + "!")
        sys.exit()
    return

def decode_file(file):
    # https://en.wikipedia.org/wiki/Intel_HEX
    with open(file, "r") as f:
        for x in range(0, os.path.getsize(file)):
            byte = f.read(1)
            if byte == ':':
                bytes = int(f.read(2), 16)
                address = int(f.read(4), 16)
                type = int(f.read(2), 16)
                if type == 0:
                    data = []
                    for bytes in range(0, bytes):
                        data.append(int(f.read(2), 16))
                    checksum = int(f.read(2), 16)
                    write_flash(address, data)
            if type == 1:
                print "End of File"
                return

init()
enter_progmode()

set_infen(0)

erase_all_flash_pages()

decode_file(sys.argv[1])

exit_progmode()
