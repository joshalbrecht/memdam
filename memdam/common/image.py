
from PIL import ImageChops
import math

import memdam

@memdam.tracer
def rmsdiff(imageA, imageB):
    '''Calculate the root-mean-square difference between two images (converted to greyscale for sanity)
    Note that if you don't convert to greyscale, there are multiple bands that come back in the histogram

    :returns: the root mean squared error of the difference between the two images. Changing just a few small things on an image gives low single digits. I'm unsure how to intuitively describe this value
    :rtype: float
    '''

    diff = ImageChops.difference(imageA.convert('L'), imageB.convert('L'))
    histogram = diff.histogram()
    squares = (value*(idx**2) for idx, value in enumerate(histogram))
    sum_of_squares = sum(squares)
    rms = math.sqrt(sum_of_squares/float(imageA.size[0] * imageA.size[1]))
    return rms
