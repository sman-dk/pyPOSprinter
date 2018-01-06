#!/usr/bin/python
# -*- coding: utf-8 -*-
# "THE BEER-WARE LICENSE" (Revision 42):
# Georg Sluyterman <georg@sman.dk> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.
# 

"""version 1.0 - a POSprinter module for Python"""
class POSprinter:
    """This module prints text, images etc. for serial connected label printers (POS printer)"""
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, bytesize=8, parity='N', stopbits=1, charWidth=44, pxWidth=284):
        """Set up serial port. Set width of of the printer/paper in number of characters and pixels."""
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
        """Write simple text string. Remember \n for newline where applicable.
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
    def printImgFromFile(self, filename, resolution="high", align="center", scale=None, rotate=None):
        """Print an image from a file.
        resolution may be set to "high" or "low". Setting it to low makes the image a bit narrow (90x60dpi instead of 180x180 dpi) unless scale is also set.
        align may be set to "left", "center" or "right".
        scale resizes the image with that factor, where 1.0 is the full width of the paper.
        rotate rotates the image (number of degrees"""
        try:
            import Image
            # Open file and convert to black/white (colour depth of 1 bit)
            img = Image.open(filename).convert("1")
            if rotate:
                img = img.rotate(rotate, expand=True)
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

    def printFontText(self, text, resolution="high", align="left", fontFile="/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-B.ttf", textSize=25, rotate=None, bgColor=255, fontColor=0, scale=None, leading=0.25, returnPILObject=False, dontPrint=False):
        """Print text as a rendered image using a truetype font. Text may be be a list of string
        objects (one object per line). If a line is too wide the function will try to line wrap.
        Arg. 'leading' is the interline spacing in as a proportion of the height of a line.
        Arg. 'scale' is the proportion of the width of the paper.
        returnPILObject returns the printed PIL Image object that is printet (or would have been printed if dontPrint is set to True."""
        import ImageFont, ImageDraw, Image
        if resolution == "high":
            currentpxWidth = self.pxWidth * 2
        font = ImageFont.truetype(fontFile, textSize)

        def splitList(currentpxWidth, txtList, font, newlineSplitOnly=False):
            """Each str/unicode in txtList equals one line when printet. Split at newlines and furthermore split if a line is too wide."""
            # First of search for newlines and split the list if a newline is found
            withoutNewlines = []
            for txt in txtList:
                withoutNewlines.extend(txt.split("\n"))
            txtList = withoutNewlines
            if newlineSplitOnly:
                return txtList

            txtListWrapped = []
            for txt in txtList:
                # If the whole line is too wide, remove words until we are good
                if font.getsize(txt)[0] > currentpxWidth:
                    txtLen = len(txt)
                    for i in range(txtLen)[::-1]:
                        if font.getsize(txt[:i+1])[0] <= currentpxWidth:
                            whitespaceEtc = [ " ", "\t", "-" ]
                            if txt[i] in whitespaceEtc:
                                txtSplit = [ txt[:i+1].rstrip(), txt[i+1:] ]
                                if font.getsize(txtSplit[1])[0] > currentpxWidth:
                                    txtSplit = splitList(currentpxWidth, txtSplit, font)
                                    break
                                else:
                                    break
                            # If there are no whitespaces etc. then split the word
                            elif not any(w in txt[:i+1] for w in whitespaceEtc):
                                if font.getsize(txt[:i+1]+"-")[0] <= currentpxWidth:
                                    txtSplit = [ txt[:i+1].rstrip()+"-", txt[i+1:] ]
                                    if font.getsize(txtSplit[1])[0] > currentpxWidth:
                                        txtSplit = splitList(currentpxWidth, txtSplit, font)
                                        break
                                    else:
                                        break
                            else:
                                continue
                else:
                    txtSplit = [ txt ]
                txtListWrapped.extend(txtSplit)
            return txtListWrapped

        # If txtList is a simple string make it a list
        if type(text) is list:
            txtList = text
        else:
            txtList = [ text ]
        # Spacing between lines as a proportion of the width of a danish letter for the current text size.
        leadingDots = int(font.getsize(u"Å")[0]*leading)
        if rotate in [ 90, 270 ]:
            # Don't wrap lines based on width when turned 90 or 270 degrees
            txtList = splitList(currentpxWidth, txtList, font, newlineSplitOnly=True)
        else:
            # Do wordwrapping etc.
            txtList = splitList(currentpxWidth, txtList, font)

        # Determine the size of the resulting text image
        size = [0,0]
        lineHeight = font.getsize("a")[1]
        size = [ 0, ( leadingDots + lineHeight ) * len(txtList) - leadingDots ]
        if rotate is 180:
            # Avoid right alignment of rotated text, if a line is less wide than the paper / currentpxWidth
            size[0] = currentpxWidth
        else:
            for txt in txtList:
                txtWidth = font.getsize(txt)[0]
                if txtWidth > size[0]:
                    size[0] = txtWidth
        # Create the actual image containing the text
        img = Image.new("1",size)
        draw = ImageDraw.Draw(img)
        draw.rectangle((0,0) + img.size,fill=bgColor)
        pointer = [0, 0]
        # For each line..
        for txt in txtList:
            draw.text(pointer, txt, font=font, fill=fontColor)
            pointer[1] += lineHeight + leadingDots

        if rotate:
            angles = [0, 90, 180, 270]
            if rotate in angles:
                img = img.rotate(rotate, expand=True)
            else:
                raise ValueError("rotate must be part of %s if set " % str(angles))
        if rotate in [90, 270]:
            if img.size[0] > currentpxWidth and not scale:
                raise Exception("The textSize is too large to print. Use either a smaller textSize or the scale parameter")
        else:
            if img.size[0] > currentpxWidth:
                raise Exception("Could not print the text. One or more lines are too wide. Did you choose a very large font?")

        if not dontPrint:
            self.printImgFromPILObject(img, resolution=resolution, align=align, scale=scale)
        if returnPILObject:
            return img

    def printLine(self, pxWidth=False, width=1.0, pxThickness=4, pxHeading=10, pxTrailing=10, resolution="high", returnPILObject=False, dontPrint=False):
        """Prints a horisontal line.
        If width is set then pxWidth is ignored. width higher than 1.0 is ignored."""
        # calculate dimensions
        if resolution == "high":
            currentpxWidth = self.pxWidth * 2
        if not pxWidth:
            pxWidth = int(currentpxWidth * width)
        import Image, ImageDraw
        pxHeight = pxHeading + pxThickness + pxTrailing
        img = Image.new("1", (currentpxWidth, pxHeight))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0,0,currentpxWidth, pxHeight), fill=255)
        draw.rectangle(((currentpxWidth - pxWidth)/2,pxHeading,(currentpxWidth - pxWidth)/2 + pxWidth,pxHeading+pxThickness), fill=0)
        if not dontPrint:
            self.printImgFromPILObject(img, resolution=resolution)
        if returnPILObject:
            return img

