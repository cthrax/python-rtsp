from optparse import OptionParser
from twisted.internet import reactor
from rtsp import RTSPClient, RTSPClientFactory
from twisted.python import failure, log
import signal
import sys

# http://blogmag.net/blog/read/38/Print_human_readable_file_size
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

def success(result):
    print "success"
    reactor.stop()

def error(failure):
    print("Failure: %s" % failure.getErrorMessage())
    reactor.stop()

def progress(factory):
    print('Downloaded %s' % sizeof_fmt(factory.data_received))
    reactor.callLater(1, progress, factory)
    
class SigHandler():
    factory = None
    def setFactory(self, factory):
        self.factory = factory
        
    def sighandler(self, signum, frame):
        if (signum == signal.SIGINT):
            print("Received sigint, terminating stream.")
            self.factory.client.sendNextMessage()
            reactor.stop()
        
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-u', '', dest='url', help='url to download',
                      metavar='URL')
    parser.add_option('-f', '', dest='file', help='file to save to',
                      metavar='FILENAME')
    options, args = parser.parse_args()
    if options.url is None:
        print('You must enter a url to download\n')
        parser.print_help()
        exit()
    if not options.file:
        options.file = re.search('[^/]*$', options.url).group(0)
    if not options.file or len(options.file) < 1:
        print('Invalid file name specified\n')
        parser.print_help()
        exit()
        
    sighandler = SigHandler()
    signal.signal(signal.SIGHUP | signal.SIGINT, sighandler.sighandler)
        
    log.startLogging(sys.stdout)
    factory = RTSPClientFactory(options.url, options.file)
    sighandler.setFactory(factory)
    factory.bandwidth = 99999999999
    factory.deferred.addCallback(success).addErrback(error)
    reactor.connectTCP(factory.host, factory.port, factory)
    reactor.callLater(1, progress, factory)
    reactor.run()
