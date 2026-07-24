with source as (
    select * from {{ source('cmc_raw', 'info') }}
),

renamed as (
    select
        id::bigint                  as coin_id,
        category::varchar           as coin_category,
        description::text            as coin_description,
        logo::varchar                 as logo_url,
        date_launched::timestamp       as date_launched_at
    from source
)

select * from renamed
