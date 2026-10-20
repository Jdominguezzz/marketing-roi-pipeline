{#
    Normalise Brazilian city names: lowercase, no accents, no "/ state" or "- sp" suffix,
    single spaces. Good enough for grouping; city is never used as a join key.
#}
{% macro clean_city(column_name) -%}
    regexp_replace(
        regexp_replace(strip_accents(lower(trim({{ column_name }}))), '\s*[/\\,-].*$', ''),
        '\s+', ' ', 'g'
    )
{%- endmacro %}
