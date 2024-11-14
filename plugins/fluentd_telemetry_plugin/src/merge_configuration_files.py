import configparser
import logging
import sys
import os

def merge_ini_files(old_file_path, new_file_path):
    # Check if files exist
    if not os.path.isfile(old_file_path):
        logging.error(f"file %s does not exist.", old_file_path)
        sys.exit(1)
    if not os.path.isfile(new_file_path):
        logging.error(f"file %s does not exist.", new_file_path)
        sys.exit(1)

    # Create a configparser object
    config_old = configparser.ConfigParser()
    config_new = configparser.ConfigParser()

    # Read the old and new files
    try:
        config_old.read(old_file_path)
        config_new.read(new_file_path)

    except configparser.Error as e:
        logging.error(f"Failed to parse configurations files: %s", e)
        sys.exit(1)

    # Merge configurations
    for section in config_new.sections():
        if not config_old.has_section(section):
            config_old.add_section(section)
        for option in config_new.options(section):
            # If option exists in the old file, retain the old value
            if not config_old.has_option(section, option):
                # Otherwise, add the new value
                config_old.set(section, option, config_new.get(section, option))

    # Write the merged configuration to the old file path
    with open(old_file_path, 'w', encoding="utf-8") as configfile:
        config_old.write(configfile)

    logging.info(f"Configuration has been merged and saved to %s", old_file_path)

if __name__ == "__main__":
    # Get file paths from command line arguments
    if len(sys.argv) != 3:
        logging.error("Usage: python merge_configuration_files.py <old_file_path> <new_file_path>")
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]

    merge_ini_files(old_file, new_file)
