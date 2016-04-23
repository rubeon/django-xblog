"""
Helper classes and utilities for testing

"""
import six
from django.test.client import Client
from datetime import datetime
try:
    from urllib.parse import parse_qs
    from urllib.parse import urlparse
    from xmlrpc.client import Transport
except ImportError:  # Python 2
    from urlparse import parse_qs
    from urlparse import urlparse
    from xmlrpclib import Transport

class TestTransport(Transport):
    """
    Handles connections to XML-RPC server through Django test client.
    """

    def __init__(self, *args, **kwargs):
        Transport.__init__(self, *args, **kwargs)
        self.client = Client()

    def request(self, host, handler, request_body, verbose=0):
        self.verbose = verbose
        response = self.client.post(handler,
                                    request_body,
                                    content_type="text/xml")
        res = six.BytesIO(response.content)
        setattr(res, 'getheader', lambda *args: '')  # For Python >= 2.7
        res.seek(0)
        return self.parse_response(res)

POST_CONTENT = {
    'post_type' : 'post',
    'post_status' : 'publish',
    'post_title' : 'A Normal Post',
    'post_author' : '',
    'post_excerpt' : '',
    'post_content' : u"<p>This is some post content.  Sweet",
    'post_date_gmt' : datetime.now(),
    'post_format' : 'standard',
    'post_name' : '',
    'post_password' : '',
    'comment_status' : 'open',
    'ping_status' : 'open',
    'sticky' : False,
    'post_thumbnail' : [],
    'post_parent' :  0,
    # 'terms' : {
    #     'mytags': [ContentType.objects.get_for_model(Tag)]
    # },
    # 'terms_names':{
    #     'mytags':["MyTagNumber1", "MyTagNumber2"],
    # },
    'enclosure': {
        'url' : '',
        'length' : '',
        'type' : '',
    }
}

POST1_PARAMS = {
    'title': "Test User 1 Post",
    'body': "This is some stuff.\n\nSome stuff, you know.",
}

USER1_PARAMS = {
    'username': 'test_user1',
    'first_name': 'Test',
    'last_name': 'User2',
    'email': 'testuser@example.com',
    'password': 'MyTestPass1',
    'is_staff': False,
    'is_superuser': False
}
USER2_PARAMS = {
    'username': 'test_user2',
    'first_name': 'Test',
    'last_name': 'User2',
    'email': 'testuser2@example.com',
    'password': 'MyTestPass2',
    'is_staff': False,
    'is_superuser': False
}

ROGUE_USER_PARAMS = {
    'username': 'rogue_user',
    'first_name': 'Rogue',
    'last_name': 'User',
    'email': 'rogueuser@example.com',
    'password': 'RoguePass1',
    'is_staff': False,
    'is_superuser': False
}

ADMIN_USER_PARAMS = {
    'username': 'admin',
    'first_name': 'Admin',
    'last_name': 'User',
    'email': 'adminuser@example.com',
    'password': 'AdminPass123',
    'is_staff': True,
    'is_superuser': True
}

TEST_BLOG_PARAMS = {
    'title':'Test User 1\'s Space',
    'description':'A blog for Test User 1.  Slippery when wet!',
}

CAT1_PARAMS = {
    'title': 'Test Category 1',
    'description': 'Category 1 meant namely for testing',
}

CAT2_PARAMS = {
    'title': 'Test Category 2',
    'description': 'Category 2 meant namely for testing',
}
