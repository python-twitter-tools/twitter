'''
    This module is automatically generated using `update.py`

    .. data:: POST_ACTIONS
        List of twitter method names that require the use of POST
'''

POST_ACTIONS = [

    # Status Methods
    'update', 'retweet', 'update_with_media',

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
    'lookup', 'report_spam',

    # Geo Methods
    'place',

    # Streaming Methods
    'filter', 'user', 'site',

    # OAuth Methods
    'token', 'access_token',
    'request_token', 'invalidate_token',
]
