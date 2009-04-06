import os
import tempfile


class ListenSome:
    
    ROBOT_LISTENER_API_VERSION = '2'
    
    def __init__(self):
        outpath = os.path.join(tempfile.gettempdir(), 'listen_some.txt')
        self.outfile = open(outpath, 'w')
        
    def startTest(self, name, attrs):
        self.outfile.write(name + '\n')

    def endSuite(self, name, attrs):
        self.outfile.write(attrs['message'] + '\n')
        
    def close(self):
        self.outfile.close()
        
        
class WithArgs(object):

    ROBOT_LISTENER_API_VERSION = '2'
    
    def __init__(self, arg1, arg2='default'):
        outpath = os.path.join(tempfile.gettempdir(), 'listener_with_args.txt')
        outfile = open(outpath, 'a')
        outfile.write("I got arguments '%s' and '%s'\n" % (arg1, arg2))
        outfile.close()
    
        
class InvalidMethods:

    ROBOT_LISTENER_API_VERSION = '2'
    
    def start_suite(self, wrong, number, of, args, here):
        pass
    
    def end_suite(self, *args):
        raise RuntimeError("Here comes an exception!")
