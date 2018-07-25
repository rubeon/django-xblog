# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
# from models import Category, Entry
import SimpleXMLRPCServer
import sys
import traceback
# dispatcher = SimpleXMLRPCServer.SimpleXMLRPCDispatcher()
import logging
logger = logging.getLogger(__name__)


def public(f):
    """ decides if a function is public or not"""
    f.public = True
    return f

def is_public(func):
    return func is not None and hasattr(func,'public') and func.public
    
def dotify(name):
    """ translates a function name with dots in it..."""
    return name.replace('_','.')
    
def list_public_methods(obj):
    """ returns a list of attribute strings, found in 
    specifiedd object, which represent callable functions..."""
    methods = SimpleXMLRPCServer.list_public_methods(obj) 
    methods = [dotify(m) for m in methods if is_public(getattr(obj,m,None))]
    return methods

def resolve_dotted_attribute(obj, attr, allow_dotted_names=True):
    """ translates xml api to python-safe api"""
    attrs = attr.split('.')
    if attrs[0].startswith('_'):
        raise AttributeError('attempt to access private attribute "%s" ' % i)

    #for in range(len(attrs),0,-1):
    for i in range(10):
        name = '_'.join(attrs[:i])
        obj0 = getattr(obj,name,None)
        if obj0:
            attrs = attrs[i:]
            if len(attrs):
                obj0 = resolve_dotted_attribute(obj0,'.'.join(attrs), allow_dotted_names)
            return obj0
        if not allow_dotted_names:
            return None

class SafeXMLRPCView(SimpleXMLRPCServer.SimpleXMLRPCDispatcher):
    """ checks for'public' attribute on callables before calling them... """
    def system_listMethods(self):
        methods = self.funcs.keys()
        if self.instance is not None:
            if hasattr(self.instance, '_listMethods'):
                methods = SimpleXMLRPCServer.remove_duplicates(
                methods + list_public_methods(self.instance)
                )
        elif not hasattr(self.instance, '_dispatch'):
            methods = SimpleXMLRPCServer.remove_duplicates(
                methods + list_public_methods(self.instance))
    system_listMethods.public = True
    
    def system_methodSignature(self, methods_name):
        """ """
        return SimpleXMLRPCView.system_methodSignature(self, method_name)
    system_methodSignature.public = True
    
    def system_methodHelp(self, method_name):
        return SimpleXMLRPCView.system_methodHelp(self, method_name)
    system_methodHelp.public=True
    
    def _dispatch(self, method, params):
        func = None
        try:
            func = self.funcs[method]
        except KeyError:
            if self.instance is not None:
                if hasattr(self.instance, '_dispatch'):
                    return apply(getattr(self.insance,'_dispatch'),
                                 (method, params)
                                 )
                else:
                    # call method directly
                    try:
                        func = resolve_dotted_attribute(self.instance, method)
                    except AttributeError:
                        pass
        if func is not None and hasattr(func, 'public') and func.public:
            return apply(func, params)
        else:
            raise Exception('method %s is not supported' % method)

@csrf_exempt
def call_xmlrpc(request, module):
    """ handles XML RPC Calls """
    # python 2.5 apparently changed the init for SimpleXMLDispatcher...
    if sys.version.startswith('2.5'):
        dispatcher = SafeXMLRPCView(False, None)
    else:
        dispatcher = SafeXMLRPCView()
    try:
        mod = __import__(module, '','',[''])
    except ImportError, e:
        raise EnvironmentError, "Could not import module %s (is it on sys.path?): %s" % (module, e)

    dispatcher.register_instance(mod)
    dispatcher.register_introspection_functions()
    
    try:
        if request.META['REQUEST_METHOD']!='POST':
            raise Exception('Non POST methods not allowed')
        logger.debug(request.META)
        # get arguments
        data = request.body
        logger.debug("XMLRPC Data:")
        logger.debug(data)
        response = dispatcher._marshaled_dispatch(
            data, getattr(mod, '_dispatch', None)
        )
    except Exception as e:
        logger.warn("Baaaa-DOING! %s" % str(e))
        response = SimpleXMLRPCServer.xmlrpclib.Fault(1, "%s:%s" % (
            sys.exc_type, sys.exc_value
            ))
    
    logger.debug(response)
    return HttpResponse(response, mimetype="text/xml")

view = call_xmlrpc

