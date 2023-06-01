"""
This is a log parser for Eyal Pitchadze for getting important log messages from events.log UFM log file.
Usage:
cat event.log | python eventor.py

or

tail -f events.log | python eventor.py

or

python eventor.py events.log
"""

import re
import sys

# Dictionary of patterns for different event types
patterns = {
    "SW-SW": {
        "pattern": r'^(?P<timestamp>[\d\-]* [\d\.:]*).*\[(?P<error_code>329|328)\].*Link (?P<state>went down|is up): \(Switch:(?P<switch1>[^ ]*).*?\).* - \(Switch:(?P<switch2>.*)\).*$',
        "message_template": "Switch:{switch1} to Switch:{switch2}"
    },
    "SW-HCA": {
        "pattern": r'^(?P<timestamp>[\d\-]* [\d\.:]*).*\[(?P<error_code>329|328)\].*Link (?P<state>went down|is up): \(Computer:(?P<hca>[^ ]*).*?\).* - \(Switch:(?P<switch>.*)\).*$',
        "message_template": "Computer:{hca} to Switch:{switch}"
    },
    "SW": {
        "pattern": r'^(?P<timestamp>[\d\-]* [\d\.:]*).*\[(?P<error_code>64|65)\].*Switch: (?P<switch>[^ ]*).*(?P<state>Out of|In) Service.*$',
        "message_template": "Switch:{switch}"
    }
}

is_down = re.compile(r"(down|out)", re.IGNORECASE)


# Function to process a line and extract the required fields
def process_line(line):
    for event_type, pattern_data in patterns.items():
        match = pattern_data["regexp"].match(line)
        if match:
            match_dict = match.groupdict()
            state = "DOWN" if re.search(is_down, match_dict['state']) else "UP"
            message = pattern_data["message_template"].format_map(match_dict)
            match_dict['message'] = message
            match_dict['state'] = state
            match_dict['event_type'] = event_type
            match_dict['original_message'] = line
#           output = ("{timestamp}\t{state:4s}\t{event_type:6s}\t[{error_code:3s}]\t{message:50s}\t{original_message}"
#                     .format_map(match_dict))
#           output = ("{timestamp}\ti{state:4s}\t{event_type:6s}\t[{error_code:3s}]\t{message:50s}"
#                      .format_map(match_dict))
            output = ("{timestamp}\t{state:4s}\t{event_type:6s}\t{message:50s}"
                      .format_map(match_dict))

            return output  # Found a match, exit the loop
    return None


def compile_patterns():
    for key in patterns.keys():
        patterns[key]['regexp'] = re.compile(patterns[key]['pattern'])


def main():
    compile_patterns()
    lines = 0
    matches = 0
    if len(sys.argv) > 1:  # eventor.py <file_name>
        f = open(sys.argv[1], 'rt')
    else:
        f = sys.stdin  # cat <file_name> | python eventor.py
    try:
        for line in f:
            lines += 1
            output = process_line(line.strip())
            if output:
                print(output)
                matches += 1
    except KeyboardInterrupt:
        print('interrupted by user')
    print(f'finished processing {lines} found {matches} matches')


if __name__ == "__main__":
    main()
