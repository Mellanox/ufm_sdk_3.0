import configparser
import logging
import sys
import os

def merge_ini_files(old_file_path, new_file_path):
    # Check if files exist
    if not os.path.isfile(old_file_path):
        logging.error("File %s does not exist.", old_file_path)
        sys.exit(1)

    if not os.path.isfile(new_file_path):
        logging.error("File %s does not exist.", new_file_path)
        sys.exit(1)

    # Create configparser objects
    config_old = configparser.ConfigParser()
    config_new = configparser.ConfigParser()
    config_merged = configparser.ConfigParser()

    # Read the old and new files
    try:
        config_old.read(old_file_path)
        config_new.read(new_file_path)
    except configparser.Error as e:
        logging.error("Failed to parse configuration files: %s", e)
        sys.exit(1)

    # Start with the new configuration as the base for the merged configuration
    for section in config_new.sections():
        config_merged.add_section(section)
        for option in config_new.options(section):
            config_merged.set(section, option, config_new.get(section, option))

    # Override values in the merged configuration with those from the old configuration
    for section in config_merged.sections():
        if config_old.has_section(section):
            for option in config_merged.options(section):
                if config_old.has_option(section, option):
                    # Compare values in old and merged, and only update if they differ
                    old_value = config_old.get(section, option)
                    merged_value = config_merged.get(section, option)
                    if old_value != merged_value:
                        # Override the value in the merged configuration
                        config_merged.set(section, option, old_value)

    # Write the merged configuration to the output file
    with open(old_file, 'w', encoding="utf-8") as configfile:
        config_merged.write(configfile)

if __name__ == "__main__":
    # Get file paths from command line arguments
    if len(sys.argv) != 3:
        logging.error("Usage: python merge_configuration_files.py <old_file_path> <new_file_path>")
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]

    merge_ini_files(old_file, new_file)