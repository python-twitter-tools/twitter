import sys
import test_sanity
import test_util

test_libs = [test_sanity, test_util]

def main():
    for l in test_libs:
        for t in dir(l):
            if t.startswith('test'):
                sys.stdout.write('%s ... ' %t)
                sys.stdout.flush()
                try:
                    getattr(l,t)()
                except Exception, e:
                    import traceback
                    traceback.print_exc()
                else:
                    sys.stdout.write('OK\n')

if __name__ == '__main__':
    main()
