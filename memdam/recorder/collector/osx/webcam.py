#!/usr/bin/env python2.7
#
# camera.py -- by Trevor Bentley (02/04/2011)
#
# This work is licensed under a Creative Commons Attribution 3.0 Unported License.
#
# Run from the command line on an Apple laptop running OS X 10.6, this script will
# take a single frame capture using the built-in iSight camera and save it to disk
# using three methods.
#
# Adapted by Caleb Reach

import sys
import os
import time
import tempfile

import objc
import QTKit
from AppKit import *
from Foundation import NSObject
from Foundation import NSTimer
from PyObjCTools import AppHelper

import memdam
import memdam.common.event
import memdam.recorder.collector.collector

class Camera(NSObject):
    def init(self):
        self = super(Camera, self).init()
        if self is None:
            return None

        self.session = None
        self.running = False

        error = None

        # Create a QT Capture session
        self.session = QTKit.QTCaptureSession.alloc().init()

        # Find iSight device and open it
        dev = QTKit.QTCaptureDevice.defaultInputDeviceWithMediaType_(QTKit.QTMediaTypeVideo)
        if not dev.open_(error):
            raise RuntimeError("Couldn't open capture device.")

        # Create an input instance with the device we found and add to session
        input = QTKit.QTCaptureDeviceInput.alloc().initWithDevice_(dev)
        if not self.session.addInput_error_(input, error):
            raise RuntimeError("Couldn't add input device.")

        # Create an output instance with a delegate for callbacks and add to session
        output = QTKit.QTCaptureDecompressedVideoOutput.alloc().init()
        output.setDelegate_(self)
        if not self.session.addOutput_error_(output, error):
            raise RuntimeError("Failed to add output delegate.")
            return

        return self

    def captureOutput_didOutputVideoFrame_withSampleBuffer_fromConnection_(self, captureOutput,
                                                                           videoFrame, sampleBuffer,
                                                                           connection):
        self.count -= 1
        if self.count >= 0: return

        self.running = False
        self.session.stopRunning() # I just want one frame

        # Get a bitmap representation of the frame using CoreImage and Cocoa calls
        ciimage = CIImage.imageWithCVImageBuffer_(videoFrame)
        bitrep = NSBitmapImageRep.alloc().initWithCIImage_(ciimage)
        bitdata = bitrep.representationUsingType_properties_(self.output_type, NSDictionary.dictionary())

        # Save image to disk using Cocoa
        bitdata.writeToFile_atomically_(self.output_path, False)

    def capture(self, output_path, output_type=NSJPEGFileType, frames_to_skip=5):
        """
        Captures an image from the camera and saves it to the given output_path.

        If a previous invocation has not yet finished, this does nothing.
        """

        # Assuming that there is only one global event loop, so we shouldn't
        # have to worry with locks

        if self.running: return True
        self.running = True
        self.output_path = output_path
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        self.output_type = output_type
        #note: this countdown skips the first few frames so that the camera can adjust brightness levels
        self.count = frames_to_skip
        self.session.startRunning()
        while not os.path.exists(self.output_path):
            time.sleep(0.2)

class WebcamCollector(memdam.recorder.collector.collector.Collector):
    """
    Collect snapshots via native OSX calls.
    """

    def start(self):
        self._camera = Camera.alloc().init()

    def _collect(self, limit):
        _, snapshot_file = tempfile.mkstemp(".png")
        self._camera.capture(snapshot_file)
        snapshot = self._save_file(snapshot_file, consume_file=True)
        memdam.log.debug("Saved " + snapshot_file)

        return [memdam.common.event.new(u"com.memdam.webcam", data__file=snapshot)]
