import struct
import wave
from os.path import join, dirname
from bitstring import BitStream
import numpy as np

from kontakt.ncw import *

if __name__ == '__main__':
    # fname= join(dirname(dirname(__file__)), 'resources/Notes-36-9HM0-36-1GKL.ncw')
    # fname= join(dirname(dirname(__file__)), 'resources/Notes-36-9HM0-B-36-IHVO-B.ncw')
    fname = join(dirname(dirname(__file__)), 'resources/Notes-56-7WKZ-56-VDW1.ncw')
    with open(fname, "rb") as input_file:
        parser = NCWParserFactory.getInstance(input_file)
        audiodata = parser.read()

    bytes_per_sample: int = int(parser.header.bits / 8)
    audiobytes = bytearray()
    try:
        for smpl_idx in range(parser.header.samples):
            for chan in range(parser.header.channels):
                audiobytes.extend(audiodata[chan][smpl_idx].to_bytes(length=24, byteorder='little', signed=True))
    except :
        print( f"Sample n°{smpl_idx}\nChannel {chan}")

    with wave.open(f"{fname}.wav", "wb") as out:


        out.setnchannels(parser.header.channels)
        out.setsampwidth(bytes_per_sample)
        out.setframerate(parser.header.samplerate)

        out.setnframes(0)
        wavdata = np.array(audiodata, dtype=np.int32)
        for sample in audiobytes:
            out.writeframes(sample)
        # for samples in zip(wavdata[0], wavdata[1]):
        #     for sample in samples:
        #         out.writeframes(sample)
