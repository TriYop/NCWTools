#!/bin/env python3

from math import ceil
from typing import NamedTuple

from bitstring import ConstBitStream

NCW_SIGNATURE1 = bytes.fromhex("01A89ED631010000")
NCW_SIGNATURE2 = bytes.fromhex("01A89ED630010000")
BLOCK_SIGNATURE = bytes.fromhex("160C9A3E")

NCW_SAMPLES = 512
MAX_CHANNELS = 6

HEADER_SIZE = 120
BLOCK_HEADER_SIZE = 16


class NCWFileHeader(NamedTuple):
    """NCW sample header."""

    signature: bytearray
    channels: int
    bits: int
    samplerate: int
    samples: int
    block_def_offset: int
    blocks_offset: int
    blocks_size: int
    num_blocks: int
    data: bytearray


class NCWBlockHeader(NamedTuple):
    signature: bytearray
    base_value: int
    bits: int
    flags: int
    zeros2: int


class NCWParser:
    def __init__(self, header: NCWFileHeader, datastream):
        self.header = header
        self.blocks = bytearray
        self.datastream = datastream

    @classmethod
    def _fill24_bits(cls, n, bits, source, base_value):
        dest = []

        for i in range(1, n):
            dd = 0
            bitsleft = 8
            bitsneeded = bits
            while bitsneeded > 0:
                dv = [base_value, base_value << 8, base_value << 16]
                print(dv)
                dest_val = 0x10000 * base_value, 0x100 * base_value + base_value
                # if bitsneeded>bitsleft:
                #    dd= = dd & 0xff
                bitsneeded = bitsneeded - bitsleft
                bitsleft = 8

    def _read_block_header(self, block_offset):

        self.datastream.seek(self.header.blocks_offset + block_offset)

        signature = self.datastream.read(4)
        if '' == signature:
            return None

        assert signature == BLOCK_SIGNATURE, f"Invalid block signature: {signature}"

        base_value = int.from_bytes(bytes=self.datastream.read(4), byteorder="little", signed=False)
        bits = int.from_bytes(bytes=self.datastream.read(2), byteorder="little", signed=False)
        flags = int.from_bytes(bytes=self.datastream.read(2), byteorder="little", signed=False)
        zeros2 = int.from_bytes(bytes=self.datastream.read(4), byteorder="little", signed=False)
        block_header = NCWBlockHeader(signature=signature, base_value=base_value, bits=bits, flags=flags, zeros2=zeros2)
        #
        # print(f"Base value: {base_value}")
        # print(f"Flags:      {flags}")
        return block_header

    def _extract(self, buffer: bytearray, nbits: int, base_value: int = 0):
        offset = 0
        bitsbuffer = ConstBitStream(bytes=buffer)
        data = []
        while offset < len(buffer) * 8:
            data.append(bitsbuffer.peek(nbits).int + base_value)
            offset += nbits
        # print(f"Loaded {len(data)} samples from block buffer")
        return data

    def _read_block_date(self, block_offset: int, nbits: int, base_value: int):
        self.datastream.seek(self.header.blocks_offset + block_offset + BLOCK_HEADER_SIZE)
        buffer = self.datastream.read(64 * nbits)

        samples = self._extract(buffer, nbits, base_value)
        return samples

    def read(self):
        pass

    def write(self):
        pass


class NCW8Parser(NCWParser):

    def __init__(self, header: NCWFileHeader, datastream):
        super(NCW8Parser, self).__init__(header, datastream)
        print("Parsing 8 bit sample data")

    def read(self):
        pass

    def write(self):
        pass


class NCW16Parser(NCWParser):
    def __init__(self, header: NCWFileHeader, datastream):
        super(NCW16Parser, self).__init__(header, datastream)
        print("Parsing 16 bit sample data")

    def read(self):
        pass

    def write(self):
        pass


class NCW24Parser(NCWParser):

    def __init__(self, header: NCWFileHeader, datastream):
        super(NCW24Parser, self).__init__(header, datastream)
        print(f"Parsing 24 bit sample data from {datastream}")

    def read(self):
        # Read header
        current_offset = 0
        current_sample = 0

        block_index = 0
        samples = [[] for chan in range(self.header.channels)]

        while current_offset < self.header.blocks_size:
            for chan in range(self.header.channels):
                block_head = self._read_block_header(current_offset)
                nbits = abs(block_head.bits) if block_head != 0 else self.header.bits
                current_offset += BLOCK_HEADER_SIZE + nbits * 64

                block_samples = self._read_block_date(current_offset, nbits, block_head.base_value)
                samples[chan].extend(block_samples)

            block_index += 1
        print(f"Extracted {len(samples[0])} samples from {len(samples)} channels")
        return samples

    def write(self):
        pass


class NCW32Parser(NCWParser):

    def __init__(self, header: NCWFileHeader, datastream):
        super(NCW32Parser, self).__init__(header, datastream)
        print("Parsing 32 bit sample data")

    def read(self):
        pass

    def write(self):
        pass


class NCWParserFactory:
    @classmethod
    def getInstance(cls, filestream) -> NCWParser:
        signature = filestream.read(8)
        channels = int.from_bytes(bytes=filestream.read(2), signed=False, byteorder="little")
        bits = int.from_bytes(bytes=filestream.read(2), signed=False, byteorder="little")
        samplerate = int.from_bytes(bytes=filestream.read(4), signed=False, byteorder="little")
        samples = int.from_bytes(bytes=filestream.read(4), signed=False, byteorder="little")
        block_def_offset = int.from_bytes(bytes=filestream.read(4), signed=False, byteorder="little")
        blocks_offset = int.from_bytes(bytes=filestream.read(4), signed=False, byteorder="little")
        blocks_size = int.from_bytes(bytes=filestream.read(4), signed=False, byteorder="little")
        data = filestream.read(88)

        header = NCWFileHeader(signature=signature,
                               channels=channels,
                               bits=bits,
                               samplerate=samplerate,
                               samples=samples,
                               block_def_offset=block_def_offset,
                               blocks_offset=blocks_offset,
                               blocks_size=blocks_size,
                               data=data,
                               num_blocks=ceil(samplerate / NCW_SAMPLES))

        assert signature in [NCW_SIGNATURE1,
                             NCW_SIGNATURE2], "Invalid signature detected. Let's continue for debug purposes"
        assert bits in [8, 16, 24, 32], "Invalid value for sample depth"

        print(f"======[ {filestream} ]======")
        print(f"Channels:         {channels}")
        print(f"Sample depth:     {bits}")
        print(f"Sample rate:      {samplerate}")
        print(f"Sample count:     {samples}")
        print(f"Block def offset: {block_def_offset}")
        print(f"Blocks offset:    {blocks_offset}")
        print(f"Blocks size:      {blocks_size}")

        if 8 == bits:
            return NCW8Parser(header, filestream)
        elif 16 == bits:
            return NCW16Parser(header, filestream)
        elif 24 == bits:
            return NCW24Parser(header, filestream)
        elif 32 == bits:
            return NCW32Parser(header, filestream)
