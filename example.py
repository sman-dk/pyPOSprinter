#!/usr/bin/python

from pyqrnative import PyQRNative
qr = PyQRNative.QRCode(5, PyQRNative.QRErrorCorrectLevel.Q)
qr.addData("http://www.sman.dk")
qr.make()
im = qr.makeImage()
ims = im.resize((525,525))
from POSprinter import POSprinter
printer = POSprinter.POSprinter()
printer.write("Hello Puffy\n", align="center")
printer.lineFeed(2)
printer.printImgFromFile("puffy.gif", resolution="low", scale=1.0)
printer.write("Friske agurker paa glas", rcolStr="200 DKK")
printer.lineFeed(2)
printer.printImgFromPILObject(ims, scale=0.5)
printer.lineFeedCut()

