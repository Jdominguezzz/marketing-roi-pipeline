select channel_month_key, conversion_rate
from {{ ref('mart_channel_roi') }}
where conversion_rate < 0 or conversion_rate > 1
