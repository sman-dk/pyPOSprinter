#!/usr/bin/python
# "THE BEER-WARE LICENSE" (Revision 42):
# Georg Sluyterman <georg@sman.dk> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.
# 

"""version 1.0 - a POSprinter module for Python"""
class POSprinter:
    """This module prints text, images etc. for serial connected label printers (POS printer)"""
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, bytesize=8, parity='N', stopbits=1, charWidth=44, pxWidth=284):
        """Set up serial port. Set width of of the printer/paper in number of characters."""
        # Multiple inheritance may become a nightmare, so we are importing the modules insted.
        try:
            import serial
        except:
            raise 
        else:
            # Set up serial port
            try:
                self.printer = serial.Serial(port, baudrate, bytesize, parity, stopbits)
            except:
                raise
        # Assign other values
        self.width = charWidth
        self.pxWidth = pxWidth

    def write(self, string, rcolStr=None, align="left"):
        r"""Write simple text string. Remember \n for newline where applicable.
        rcolStr is a righthand column that may be added (e.g. a price on a receipt). Be aware that when rcolStr is used newline(s) may only be a part of rcolStr, and only as the last character(s)."""
        if align != "left" and len(string) < self.width:
            blanks = 0
            if align == "right":
                blanks = self.width - len(string.rstrip("\n"))
            if align == "center":
                blanks = ( self.width - len(string.rstrip("\n")) ) / 2
            string = " " * blanks + string
                
        if not rcolStr:
            try:
                self.printer.write(string)
            except:
                raise
        else:
            rcolStrRstripNewline = rcolStr.rstrip("\n")
            if "\n" in string or "\n" in rcolStrRstripNewline:
                raise ValueError("When using rcolStr in POSprinter.write only newline at the end of rcolStr is allowed and not in string (the main text string) it self.")
            # expand string
            lastLineLen = len(string)%self.width + len(rcolStrRstripNewline)
            if lastLineLen > self.width:
                numOfBlanks = ( self.width - lastLineLen ) % self.width
                string += numOfBlanks * " "
                lastLineLen = len(string)%self.width + len(rcolStrRstripNewline)
            if lastLineLen < self.width:
                numOfBlanks = self.width - lastLineLen
                string += " " * numOfBlanks
            try:
                self.printer.write(string + rcolStr)
            except:
                raise

    def lineFeed(self, times=1, cut=False):
        """Write newlines and optional cut paper"""
        while times:
            try:
                self.write("\n")
            except:
                raise
            times -= 1
        if cut:
            try:
                self.cut()
            except:
                raise

    def lineFeedCut(self, times=6, cut=True):
        """Enough line feed for the cut to be beneath the previously printed text etc."""
        try:
            self.lineFeed(times, cut)
        except:
            raise

    def cut(self):
        """Cut paper. You probably want to use lineFeedCut() in most situations."""
        try:
            self.write("\x1D\x56\x00")
        except:
            raise

    def close(self):
        """Close the connection to the serial printer"""
        try:
            self.printer.close()
        except:
            raise
    def printImgFromFile(self, filename, resolution="high", align="center", scale=None):
        """Print an image from a file.
        resolution may be set to "high" or "low". Setting it to low makes the image a bit narrow (90x60dpi instead of 180x180 dpi) unless scale is also set.
        align may be set to "left", "center" or "right".
        scale resizes the image with that factor, where 1.0 is the full width of the paper."""
        try:
            import Image
            # Open file and convert to black/white (colour depth of 1 bit)
            img = Image.open(filename).convert("1")
            self.printImgFromPILObject(img, resolution, align, scale)
        except:
            raise
    def printImgFromPILObject(self, imgObject, resolution="high", align="center", scale=None):
        """The object must be a Python ImageLibrary object, and the colordepth should be set to 1."""
        try:
            # If a scaling factor has been indicated
            if scale:
                assert type(scale)==float
                if scale > 1.0 or scale <= 0.0:
                    raise ValueError, "scale: Scaling factor must be larger than 0.0 and maximum 1.0"
                # Give a consistent output regardless of the resolution setting
                scale *= self.pxWidth/float(imgObject.size[0])
                if resolution is "high":
                    scaleTuple = (  scale * 2, scale * 2 )
                else:
                    scaleTuple = ( scale, scale * 2/3.0 )
                # Convert to binary colour depth and resize
                imgObjectB = imgObject.resize( [ int(scaleTuple[i] * imgObject.size[i]) for i in range(2) ] ).convert("1")
            else:
                # Convert to binary colour depth
                imgObjectB = imgObject.convert("1")
            # Convert to a pixel access object
            imgMatrix = imgObjectB.load()
            width  = imgObjectB.size[0]
            height = imgObjectB.size[1]
            # Print it
            self.printImgMatrix(imgMatrix, width, height, resolution, align)
        except:
            raise
    def printImgMatrix(self, imgMatrix, width, height, resolution, align):
        """Print an image as a pixel access object with binary colour."""
        if resolution == "high":
            scaling = 24
            currentpxWidth = self.pxWidth * 2
        else:
            scaling = 8
            currentpxWidth = self.pxWidth
        if width > currentpxWidth:
            raise ValueError("Image too wide. Maximum width is configured to be " + str(currentpxWidth) + "pixels. The image is " + str(width) + " pixels wide.")
        for yScale in range(-(-height/scaling)):
            # Set mode to hex and 8-dot single density (60 dpi).
            if resolution == "high":
                outList = [ "0x1B", "0x2A", "0x21" ]
            else:
                outList = [ "0x1B", "0x2A", "0x00" ]
            # Add width to the communication to the printer. Depending on the alignment we count that in and add blank vertical lines to the outList
            if align == "left":
                blanks = 0
            if align == "center":
                blanks = ( currentpxWidth - width ) / 2
            if align == "right":
                blanks = currentpxWidth - width
            highByte  = ( width + blanks ) / 256
            lowByte = ( width + blanks )% 256
            outList.append(hex(lowByte))
            outList.append(hex(highByte))
            if resolution == "high":
                blanks *= 3
            if align == "left":
                pass
            if align == "center":
                for i in range(blanks):
                    outList.append(hex(0))
            if align == "right":
                for i in range(blanks):
                    outList.append(hex(0))
            for x in range(width):
                # Compute hex string for one vertical bar of 8 dots (zero padded from the bottom if necessary).
                binStr = ""
                for y in range(scaling):
                    # Indirect zero padding. Do not try to extract values from images beyond its size.
                    if ( yScale * scaling + y ) < height:
                        binStr += "0" if imgMatrix[x, yScale * scaling + y] == 255 else "1" 
                    # Zero padding
                    else:
                        binStr += "0"
                outList.append(hex(int(binStr[0:8], 2)))
                if resolution == "high":
                    outList.append(hex(int(binStr[8:16], 2)))
                    outList.append(hex(int(binStr[16:24], 2)))
            for element in outList:
                try:
                    self.write(chr(int(element, 16)))
                except:
                    raise
            try:
                self.write("\n")
            except:
                raise
