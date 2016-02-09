XBlog is a social blogging application for your site.

It can allow authenticated users to post articles and links in their own spaces, and share their thoughts with site visitors.  Users can be authenticated using Twitter, Facebook, GitHub, or a host of other social networks using [Python Social Auth][social].

It offers the following features:

* Posts
* Links
* [Pingbacks / trackbacks]
* [Markdown][markdown] Support
* [Python Social Auth][social] support
* Multiple blogs and authors
* [Haystack][haystack] integration
* API support for [WordPress][wpapi], [MetaWeblog][mwapi], [Blogger][bloggerapi], and 
[MovableType][mtapi]-compatible clients [^1]
* Integrates smoothly with Django storage backends like S3, Filesystem, and Rackspace CloudFiles

XBlog is developed in the open at https://github.com/rubeon/django-xblog/.

Many ideas and best practices for both Python and Django were gleaned from the great work on [Zinnia][zinnia], so big props to [Fantomas42][fantomas].

Testing is provided by [Drone.IO][drone]

[trackbacks]:https://en.wikipedia.org/wiki/Trackback
[haystack]:http://haystacksearch.org
[wpapi]:https://codex.wordpress.org/XML-RPC_WordPress_API
[mwapi]:https://en.wikipedia.org/wiki/MetaWeblog
[bloggerapi]:https://codex.wordpress.org/XML-RPC_Blogger_API
[mtapi]:https://codex.wordpress.org/XML-RPC_MovableType_API
[drone]:http://drone.io/
[fantomas]:http://fantomas.site/blog/
[zinnia]:https://github.com/Fantomas42/django-blog-zinnia/\
[markdown]:https://en.wikipedia.org/wiki/Markdown
[social]:https://python-social-auth.readthedocs.org/en/latest/
[^1]:Tested using [DeskPM][http://desk.pm] and [ecto][http://ecto.kung-foo.tv]
