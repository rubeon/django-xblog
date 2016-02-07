# WordPress API

This section covers the XMLRPC API hierarchy under wp.*

## wp.getPost

Retrieve a post of any registered post type.

Added in WordPress 3.4.

### Parameters
* int blog_id
* string username
* string password
* int post_id
* array fields: Optional. List of field or meta-field names to include in response.

### Return Values
* struct: Note that the exact fields returned depends on the fields parameter.
* string post_id
* string post_title
* datetime post_date
* datetime post_date_gmt
* datetime post_modified
* datetime post_modified_gmt
* string post_status
* string post_type
* string post_format
* string post_name
* string post_author1 author id
* string post_password
* string post_excerpt
* string post_content
* string post_parent
* string post_mime_type
* string link
* string guid
* int menu_order
* string comment_status
* string ping_status
* bool sticky
* struct post_thumbnail1: See wp.getMediaItem.
* array terms
    * struct: See wp.getTerm
* array custom_fields
    * struct
        * string id
        * string key
        * string value
* struct enclosure
    * string url
    * int length
    * string type

## wp.getPosts
Retrieve list of posts of any registered post type.

Added in WordPress 3.4.

### Parameters

* int blog_id
* string username
* string password
* struct filter: Optional.
    * string post_type
    * string post_status
    * int number
    * int offset
    * string orderby
    * string order
* array fields: Optional. See #wp.getPost.

### Return Values

* array
    * struct: See #wp.getPost.

 
## wp.newPost

Create a new post of any registered post type.

Added in WordPress 3.4.

### Parameters
* int blog_id
* string username
* string password
* struct content
    * string post_type
    * string post_status
    * string post_title
    * int post_author
    * string post_excerpt
    * string post_content
    * datetime post_date_gmt | post_date
    * string post_format
    * string post_name: Encoded URL (slug)
    * string post_password
    * string comment_status
    * string ping_status
    * int sticky
    * int post_thumbnail
    * int post_parent
    * array custom_fields
        * struct
            * string key
            * string value
* struct terms: Taxonomy names as keys, array of term IDs as values.
* struct terms_names: Taxonomy names as keys, array of term names as values.
* struct enclosure
* string url
* int length
* string type
* any other fields supported by wp_insert_post

### Return Values

string post_id

### Errors

**401**

* If the user does not have the edit_posts cap for this post type.
* If user does not have permission to create post of the specified post_status.
* If post_author is different than the user's ID and the user does not have the edit_others_posts cap for this post type.
* If sticky is passed and user does not have permission to make the post sticky, regardless if sticky is set to 0, 1, false or true.
* If a taxonomy in terms or terms_names is not supported by this post type.
* If terms or terms_names is set but user does not have assign_terms cap.
* If an ambiguous term name is used in terms_names.

**403**

* If invalid post_type is specified.
* If an invalid term ID is specified in terms.

**404**

* If no author with that post_author ID exists.
* If no attachment with that post_thumbnail ID exists. 

## wp.getTaxonomies

### Parameters

* int `blog_id`
* string `username`
* string `password`

### Return

* array
    * struct:
        * string `name`
        * string `label`
        * bool `hierarchical`
        * bool `public`
        * bool `show_ui`
        * bool `_builtin`
        * struct `labels`
        * struct `cap`
        * array `object_type`

### Example
WordPress.com :

Call: 
```python

     s.wp.getTaxonomies(blog['blogid'], api['username'], api['password'])

```
Result:
```python

    [{'_builtin': True,
      'cap': {'assign_terms': 'edit_posts',
              'delete_terms': 'manage_categories',
              'edit_terms': 'manage_categories',
              'manage_terms': 'manage_categories'},
      'hierarchical': True,
      'label': 'Categories',
      'labels': {'add_new_item': 'Add New Category',
                 'add_or_remove_items': '',
                 'all_items': 'All Categories',
                 'choose_from_most_used': '',
                 'edit_item': 'Edit Category',
                 'items_list': 'Categories list',
                 'items_list_navigation': 'Categories list navigation',
                 'menu_name': 'Categories',
                 'name': 'Categories',
                 'name_admin_bar': 'category',
                 'new_item_name': 'New Category Name',
                 'no_terms': 'No categories',
                 'not_found': 'No categories found.',
                 'parent_item': 'Parent Category',
                 'parent_item_colon': 'Parent Category:',
                 'popular_items': '',
                 'search_items': 'Search Categories',
                 'separate_items_with_commas': '',
                 'singular_name': 'Category',
                 'update_item': 'Update Category',
                 'view_item': 'View Category'},
      'name': 'category',
      'object_type': ['post'],
      'public': True,
      'show_ui': True},
     {'_builtin': True,
      'cap': {'assign_terms': 'edit_posts',
              'delete_terms': 'manage_categories',
              'edit_terms': 'manage_categories',
              'manage_terms': 'manage_categories'},
      'hierarchical': False,
      'label': 'Tags',
      'labels': {'add_new_item': 'Add New Tag',
                 'add_or_remove_items': 'Add or remove tags',
                 'all_items': 'All Tags',
                 'choose_from_most_used': 'Choose from the most used tags',
                 'edit_item': 'Edit Tag',
                 'items_list': 'Tags list',
                 'items_list_navigation': 'Tags list navigation',
                 'menu_name': 'Tags',
                 'name': 'Tags',
                 'name_admin_bar': 'post_tag',
                 'new_item_name': 'New Tag Name',
                 'no_terms': 'No tags',
                 'not_found': 'No tags found.',
                 'parent_item': '',
                 'parent_item_colon': '',
                 'popular_items': 'Popular Tags',
                 'search_items': 'Search Tags',
                 'separate_items_with_commas': 'Separate tags with commas',
                 'singular_name': 'Tag',
                 'update_item': 'Update Tag',
                 'view_item': 'View Tag'},
      'name': 'post_tag',
      'object_type': ['post'],
      'public': True,
      'show_ui': True},
     {'_builtin': True,
      'cap': {'assign_terms': 'edit_posts',
              'delete_terms': 'manage_categories',
              'edit_terms': 'manage_categories',
              'manage_terms': 'manage_categories'},
      'hierarchical': False,
      'label': 'Format',
      'labels': {'add_new_item': 'Add New Tag',
                 'add_or_remove_items': 'Add or remove tags',
                 'all_items': 'Format',
                 'archives': 'Format',
                 'choose_from_most_used': 'Choose from the most used tags',
                 'edit_item': 'Edit Tag',
                 'items_list': 'Tags list',
                 'items_list_navigation': 'Tags list navigation',
                 'menu_name': 'Format',
                 'name': 'Format',
                 'name_admin_bar': 'Format',
                 'new_item_name': 'New Tag Name',
                 'no_terms': 'No tags',
                 'not_found': 'No tags found.',
                 'parent_item': '',
                 'parent_item_colon': '',
                 'popular_items': 'Popular Tags',
                 'search_items': 'Search Tags',
                 'separate_items_with_commas': 'Separate tags with commas',
                 'singular_name': 'Format',
                 'update_item': 'Update Tag',
                 'view_item': 'View Tag'},
      'name': 'post_format',
      'object_type': ['post'],
      'public': True,
      'show_ui': False},
     {'_builtin': False,
      'cap': {'assign_terms': 'edit_posts',
              'delete_terms': 'manage_categories',
              'edit_terms': 'manage_categories',
              'manage_terms': 'manage_categories'},
      'hierarchical': False,
      'label': 'Xposts',
      'labels': {'add_new_item': 'Add New Tag',
                 'add_or_remove_items': 'Add or remove tags',
                 'all_items': 'Xposts',
                 'archives': 'Xposts',
                 'choose_from_most_used': 'Choose from the most used tags',
                 'edit_item': 'Edit Tag',
                 'items_list': 'Tags list',
                 'items_list_navigation': 'Tags list navigation',
                 'menu_name': 'Xposts',
                 'name': 'Xposts',
                 'name_admin_bar': 'Xposts',
                 'new_item_name': 'New Tag Name',
                 'no_terms': 'No tags',
                 'not_found': 'No tags found.',
                 'parent_item': '',
                 'parent_item_colon': '',
                 'popular_items': 'Popular Tags',
                 'search_items': 'Search Tags',
                 'separate_items_with_commas': 'Separate tags with commas',
                 'singular_name': 'Xposts',
                 'update_item': 'Update Tag',
                 'view_item': 'View Tag'},
      'name': 'xposts',
      'object_type': ['post'],
      'public': True,
      'show_ui': False},
     {'_builtin': False,
      'cap': {'assign_terms': 'edit_posts',
              'delete_terms': 'manage_categories',
              'edit_terms': 'manage_categories',
              'manage_terms': 'manage_categories'},
      'hierarchical': False,
      'label': 'Mentions',
      'labels': {'add_new_item': 'Add New Tag',
                 'add_or_remove_items': 'Add or remove tags',
                 'all_items': 'Mentions',
                 'archives': 'Mentions',
                 'choose_from_most_used': 'Choose from the most used tags',
                 'edit_item': 'Edit Tag',
                 'items_list': 'Tags list',
                 'items_list_navigation': 'Tags list navigation',
                 'menu_name': 'Mentions',
                 'name': 'Mentions',
                 'name_admin_bar': 'Mentions',
                 'new_item_name': 'New Tag Name',
                 'no_terms': 'No tags',
                 'not_found': 'No tags found.',
                 'parent_item': '',
                 'parent_item_colon': '',
                 'popular_items': 'Popular Tags',
                 'search_items': 'Search Tags',
                 'separate_items_with_commas': 'Separate tags with commas',
                 'singular_name': 'Mentions',
                 'update_item': 'Update Tag',
                 'view_item': 'View Tag'},
      'name': 'mentions',
      'object_type': ['post'],
      'public': True,
      'show_ui': False}]
      
```