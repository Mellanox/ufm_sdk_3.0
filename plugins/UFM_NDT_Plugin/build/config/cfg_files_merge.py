"""
This module is a utility for merging 2 configuration files -
the script is merging the old configuration file into the new configuration file
and writing the final merged output into results file.

@copyright:
        Copyright (C) Mellanox Technologies Ltd. 2001-2020.   ALL RIGHTS RESERVED.

        This software product is a proprietary product of Mellanox Technologies Ltd.
        (the "Company") and all right, title, and interest in and to the software product,
        including all associated intellectual property rights, are and shall
        remain exclusively with the Company.

        This software product is governed by the End User License Agreement
        provided with the software product.
"""
import os
import sys
import re
import configparser


def usage():
    print("""Parameters should be:
             1 - new configuration file name
             2 - old configuration file name
             3 - result file name
             All the names should contain full path.
          """)


def parse(line):
    # remove spaces
    line = line.strip()
    # split non-comment/comment
    keyvalue_comment = re.split(r"\s*(?<!\\)#\s*", line, 1)
    # ensure add empty comment if not exists
    if len(keyvalue_comment) == 1:
        keyvalue_comment.append("")
    # unescape non-comment
    key_value = keyvalue_comment[0]
    comment = keyvalue_comment[1]
    # get key and value
    key_value = re.split(r"\s*=\s*", key_value, 1)
    # add value if missing
    if len(key_value) == 1:
        key_value.append("")
    # create 3-tuple: (key, value, comment)
    return (key_value[0], key_value[1], comment)


def createCfgLine(key, value):
    line = "%s=%s\n" % (key, value)
    return line


help_keys = ('-h', '--h', '-help', '--help')
if sys.argv[1] in help_keys or len(sys.argv) < 4:
    usage()
    sys.exit(1)

new_file_name = sys.argv[1]
old_file_name = sys.argv[2]
for filename in (new_file_name, old_file_name):
    if not os.path.exists(new_file_name):
        print(("ERROR. File %s not exist" % filename))
        sys.exit(1)

result_file_name = sys.argv[3]

conf = configparser.ConfigParser()
conf.optionxform = str
conf.read([old_file_name])
old_sections = conf.sections()
sectionRegEx = re.compile(r'^\[(.+)\]$')
is_new_section = False
section = None

try:
    fo = open(result_file_name, 'w')
except Exception as exc:
    print(("Failed open %s file, %s" % (result_file_name, exc)))
    sys.exit(1)

try:
    with open(new_file_name, 'r') as fi:
        for line in fi:
            match = sectionRegEx.search(line)
            # section name line
            if match:
                is_new_section = False
                section = match.group(1)
                # new section
                if not conf.has_section(section):
                    is_new_section = True
            # known section
            elif section and not is_new_section:
                # pattern: key = value #comment
                key, value, comment = parse(line)
                if key and conf.has_option(section, key):
                    old_value = conf.get(section, key)
                    if old_value != value:
                        # key = old_value
                        line = createCfgLine(key, old_value)
                # pattern: #key = value
                elif not key and not value and comment:
                    c_key, c_value, c_comment = parse(comment)
                    if c_key and conf.has_option(section, c_key):
                        old_value = conf.get(section, c_key)
                        # key = old_value
                        line = createCfgLine(c_key, old_value)
            fo.write(line)
finally:
    fo.close()
