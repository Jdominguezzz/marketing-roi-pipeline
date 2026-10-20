select channel, display_name, channel_group, is_paid
from {{ ref('channel_map') }}
