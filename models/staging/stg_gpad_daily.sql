select
    row_data ->> 'SUB_ICB_LOCATION_CODE' as sub_icb_code,
    row_data ->> 'SUB_ICB_LOCATION_ONS_CODE' as sub_icb_ons_code,
    row_data ->> 'SUB_ICB_LOCATION_NAME' as sub_icb_name,
    row_data ->> 'ICB_ONS_CODE' as icb_ons_code,
    row_data ->> 'REGION_ONS_CODE' as region_ons_code,
    to_date(row_data ->> 'Appointment_Date', 'DDMONYYYY') as appointment_date,
    row_data ->> 'APPT_STATUS' as appointment_status,
    row_data ->> 'HCP_TYPE' as hcp_type,
    row_data ->> 'APPT_MODE' as appointment_mode,
    row_data ->> 'TIME_BETWEEN_BOOK_AND_APPT' as booking_lead_time,
    (row_data ->> 'COUNT_OF_APPOINTMENTS')::bigint as appointment_count,
    md5(concat_ws('|',
        row_data ->> 'SUB_ICB_LOCATION_CODE',
        row_data ->> 'Appointment_Date',
        row_data ->> 'APPT_STATUS',
        row_data ->> 'HCP_TYPE',
        row_data ->> 'APPT_MODE',
        row_data ->> 'TIME_BETWEEN_BOOK_AND_APPT'
    )) as source_native_key,
    source_hash,
    source_member,
    row_number
from {{ source('raw', 'source_row') }}
where dataset_id = 'gpad-daily-june-2026'
  and source_member <> 'APPOINTMENTS_GP_COVERAGE.csv'
