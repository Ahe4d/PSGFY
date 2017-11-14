from __future__ import print_function
import shutil, os, argparse, struct, sys, unicodedata, re
from s2 import decompile


def xor_strings(xs, ys):
    return "".join(chr(ord(x) ^ ord(y)) for x, y in zip(xs, ys))

def bytes_xor(a, b) :
    return bytes(x ^ y for x, y in zip(a, b))

def sxor(a, b):  # xor two strings of different lengths
    if len(a) > len(b):
        return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a[:len(b)], b)])
    else:
        return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a, b[:len(a)])])

all_chars = (unichr(i) for i in xrange(0x110000))
# or equivalently and much more efficiently
control_chars = ''.join(map(unichr, range(1,32) + range(127,160)))

control_char_re = re.compile('[%s]' % re.escape(control_chars))

def remove_control_chars(s):
    return control_char_re.sub('', s)

class DSOFile:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.version, = struct.unpack("I", f.read(4))
            print(self.version)
            if(self.version != 210):
                return
            all_chars = (unichr(i) for i in xrange(0x110000))
# or equivalently and much more efficiently
            control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))

            print("Reading size")
            size = struct.unpack("=I", f.read(4))[0]
            print(size)
            print("Reading global string table")
            if size:
                self.global_string_table = f.read(size)
                self.global_string_size = size
                print("Decrypting global string table")
                self.global_string_table = self.decrypt(self.global_string_table, size)
                #self.global_string_table = remove_control_chars(self.global_string_table)
               # print(self.global_string_table)

            print("Reading global float table")
            size = struct.unpack("=I", f.read(4))[0]
            if size:
                print(size)
                self.global_float_table = []
                self.read_function_floats(f, 1, size)
                print(self.global_float_table)

            print("Reading function string table")
            size, = struct.unpack("I", f.read(4))
            if size:
                print(size)
                self.function_string_table = f.read(size)
                self.function_string_table = self.decrypt(self.function_string_table, size)
                #self.function_string_table = remove_control_chars(self.function_string_table)

            print("Reading function float table")
            size = struct.unpack("=I", f.read(4))[0]
            if size:
                print(size)
                self.function_float_table = []
                self.read_function_floats(f, 0, size)
                #print(self.function_float_table)

            self.code = []
            self.linebreak_pairs = []
            print("Reading code")
            self.read_code(f)
            print("Patching string references...")
            self.patch_string_references(f)
            ##I WROTE LIKE 1/4TH OF THE CODE HERE

    @staticmethod
    def dump_string_table(st):
        return [s.encode('string_escape') for s in st.split("\x00")]

    def read_function_floats(self, fd, swi, size):
        def read_ft(ft_size, fd):
            ft = []
            print(ft_size)
            for i in range(0, ft_size):
                f, = struct.unpack("d", fd.read(8))
                ft.append(f)
            return ft

        if swi:
            self.global_float_table = read_ft(size, fd)
        else:
            self.function_float_table = read_ft(size, fd)


    def decrypt(self, o, s):
        key = "cl3buotro"
        p = ""
        for i in range(s):
            p += sxor(o[i], key[i % 9])

        return p
            #print(cache)


    def read_code(self, fd):
        """
        Reads the file's bytecode.
        """
        code_size = struct.unpack("I", fd.read(4))[0]
        line_break_pair_count = struct.unpack("I", fd.read(4))[0]
        # The code size is a number of opcodes and arguments, not a number of bytes.
        count = 0
        for i in range(code_size):
            value, = struct.unpack("B", fd.read(1))
            count += 1
            if value == 0xFF:
                value = struct.unpack("I", fd.read(4))[0]
            self.code.append(value)
            #print(value)

        count = 0
        while count < line_break_pair_count * 2:
            value, = struct.unpack("I", fd.read(4))
            count += 1
            self.linebreak_pairs.append(value)

    def get_string(self, offset, in_function=False):
        """
        Returns the value located at the given offset in a stringtable.
        """
        if not in_function:
            st = self.global_string_table
        else:
            st = self.function_string_table
        blah = st[offset:st.find("\x00", offset)].encode('string-escape').replace("\\x0", "\c").rstrip('\n')
        return blah

    def get_float(self, pos, in_function = False):
        """
        Returns the value located at the given position in a FloatTable.
        """
        if not in_function:
            ft = self.global_float_table
        else:
            ft = self.function_float_table
        return ft[pos]

    def patch_string_references(self, fd):
        """
        The IdentTable contains a list of code locations where each String is used.
        Their offset into the StringTable has to be patched in the code where zero values
        have been set as placeholders.
        """
        size, = struct.unpack("I", fd.read(4))
        for i in range(0, size):
            offset, count = struct.unpack("II", fd.read(8))
            for j in range(0, count):
                location_to_patch, = struct.unpack("I", fd.read(4))
                self.code[location_to_patch] = offset

def main():
    parser = argparse.ArgumentParser(description="Decompile DSO files.")
    parser.add_argument("file", metavar='file', nargs="+", help="The DSO file to decompile.")
    parser.add_argument("--nofolder", action="store_true", help="Turn off exporting to folders.")
    parser.add_argument("--stdout", action="store_true", help="Dump the decompiled script to stdout.")
    args = parser.parse_args()
        
   # sys.argv[1] = "./main.cs.dso"
    for f in args.file:
        # Verify that the file exists.
        if not os.path.exists(f):
            print("{!] Error: could not find %s" % f, file=sys.stderr)
            continue
        if not f.endswith(".cs.dso"):
            print("{!] Error: please run this on a dso.", file=sys.stderr)
            continue
        
        outdir = "%s-decompiled" % f[:-7]
        if not args.nofolder:
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            print(outdir)
            print("%s\%s" % (outdir, f))

        # Set the output filename
        print(f)
        if args.stdout:
            out = sys.stdout
        else:
            if f.endswith(".cs.dso") and not args.nofolder:
                outfile = "%s/" % outdir + "vars.cs"  # file.cs.dso -> file.cs
            elif not args.nofolder:
                outfile = "%s/%s.cs" % (outdir, f)  # file -> file.cs
            elif f.endswith(".cs.dso"):
                outfile = f[:-4]  # file.cs.dso -> file.cs
            else:
                outfile = "%s.cs" % f  # file -> file.cs
            out = open(outfile, 'w')

        # Create a backup of the original DSO in case the decompiled one is broken.
        if not os.path.exists("%s.bak" % f) and not args.stdout:
            shutil.copy(f, "%s.bak" % f)
        else:
            f = "%s.bak" % f  # Work on the original DSO instead of possibly decompiling our own file.

        # Decompile the file
        if sys.argv[1] == "--nofolder":
            dso = DSOFile(sys.argv[2])
        else:
            dso = DSOFile(sys.argv[1])
        try:
            no = args.nofolder
            decompile(dso, sink=out, offset=0, outdir=outdir, nofolder=no)
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()
            if tb is not None:
                prev = tb
                curr = tb.tb_next
                while curr is not None:
                    prev = curr
                    curr = curr.tb_next
                    if "ip" in prev.tb_frame.f_locals and "offset" in prev.tb_frame.f_locals:
                        break
                if "ip" in prev.tb_frame.f_locals:
                    ip = prev.tb_frame.f_locals["ip"]
                    opcode = prev.tb_frame.f_locals["opcode"]
                    print("Error encountered at ip=%d (%s) while decompiling %s." % (ip, opcode, f), file=sys.stderr)
                out.close()
                if not args.stdout:
                    pass
                    #os.remove(outfile)
            raise
        if not args.stdout:
            out.close()
            print("%s successfully decommpiled to %s." % (f, outfile))
            if os.path.exists("%s.bak" % f):
                os.remove("%s.bak" % f)
            if os.path.exists("%s.bak" % outfile):
                os.remove("%s.bak" % outfile)


if __name__ == "__main__":
    main()
