import glob
import sys
import os
import subprocess

def find_all_unittests():
    return glob.glob('**/test_*.py', recursive=True)

def run_all_unittests(tests):
    reports = []
    ret = 0
    env = 'PYTHONPATH="${PYTHONPATH}:' + os.environ['WORKSPACE'] + '/src/"'

    for test in tests:
        return_code, output = subprocess.getstatusoutput('{} python3 {}'.format(env, test))
        ret += return_code
        reports.append((return_code, test, output))

    return ret, reports

def print_reports(reports):
    for ret, test, output in reports:
        print('')
        print('=' * 120)
        print('file: {} (return code: {})'.format(test, ret))
        print('')
        print(output)
        print('')

def main():
    tests = find_all_unittests()
    ret, reports = run_all_unittests(tests)
    print_reports(reports)
    sys.exit(ret)

if __name__ == '__main__':
    main()