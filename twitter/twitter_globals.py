'''
    .. data:: POST_ACTIONS
        List of twitter method names that require the use of POST
'''

POST_ACTIONS = [

    # Status Methods
    'update', 'retweet', 'update_with_media', 'statuses/lookup',

    # Direct Message Methods
    'new',

    # Account Methods
    'update_profile_image', 'update_delivery_device', 'update_profile',
    'update_profile_background_image', 'update_profile_colors',
    'update_location', 'end_session', 'settings',
    'update_profile_banner', 'remove_profile_banner',

    # Notification Methods
    'leave', 'follow',

    # Status Methods, Block Methods, Direct Message Methods,
    # Friendship Methods, Favorite Methods
    'destroy', 'destroy_all',

    # Block Methods, Friendship Methods, Favorite Methods
    'create', 'create_all',

    # Users Methods
    'users/lookup', 'report_spam',

    # Streaming Methods
    'filter', 'user', 'site',

    # OAuth Methods
    'token', 'access_token',
    'request_token', 'invalidate_token',

    # Upload Methods
    'media/upload', 'media/metadata/create',
    
    # Collections Methods
    'collections/create', 'collections/destroy', 'collections/update',
    'collections/entries/add', 'collections/entries/curate',
    'collections/entries/move', 'collections/entries/remove'
]
