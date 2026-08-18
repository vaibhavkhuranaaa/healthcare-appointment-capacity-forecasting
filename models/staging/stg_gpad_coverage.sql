select
    row_data ->> 'SUB_ICB_LOCATION_CODE' as sub_icb_code,
    to_date(row_data ->> 'Appointment_Month', 'DDMONYYYY') as appointment_month,
    (row_data ->> 'Included Practices')::integer as included_practices,
    (row_data ->> 'Open Practices')::integer as open_practices,
    (row_data ->> 'Patients registered at included practices')::bigint as included_patients,
    (row_data ->> 'Patients registered at open practices')::bigint as open_patients,
    (row_data ->> 'Patients registered at included practices')::numeric
        / nullif((row_data ->> 'Patients registered at open practices')::numeric, 0)
        as population_coverage
from {{ source('raw', 'source_row') }}
where dataset_id = 'gpad-daily-june-2026'
  and source_member = 'APPOINTMENTS_GP_COVERAGE.csv'
