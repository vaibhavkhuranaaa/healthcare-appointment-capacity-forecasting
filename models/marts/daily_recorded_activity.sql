with activity as (
    select
        sub_icb_code,
        min(sub_icb_ons_code) as sub_icb_ons_code,
        min(sub_icb_name) as sub_icb_name,
        min(icb_ons_code) as icb_ons_code,
        min(region_ons_code) as region_ons_code,
        appointment_date,
        sum(appointment_count) as recorded_appointments,
        sum(appointment_count) filter (where appointment_status = 'Attended') as attended_appointments,
        sum(appointment_count) filter (where appointment_status = 'DNA') as dna_appointments,
        sum(appointment_count) filter (where appointment_status = 'Unknown') as unknown_status_appointments
    from {{ ref('stg_gpad_daily') }}
    group by sub_icb_code, appointment_date
),
coverage as (
    select * from {{ ref('stg_gpad_coverage') }}
)
select
    activity.*,
    coverage.population_coverage,
    coverage.included_practices,
    coverage.open_practices
from activity
left join coverage
  on activity.sub_icb_code = coverage.sub_icb_code
 and date_trunc('month', activity.appointment_date) = coverage.appointment_month
