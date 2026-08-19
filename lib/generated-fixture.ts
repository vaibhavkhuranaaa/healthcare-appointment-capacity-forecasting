export type ForecastDay = {
  date: string;
  p10: number;
  p50: number;
  p90: number;
};

export type ObservedDay = { date: string; value: number };

export const generatedForecast: ForecastDay[] = Array.from({ length: 28 }, (_, index) => {
  const date = new Date(Date.UTC(2026, 6, 1 + index));
  const weekday = date.getUTCDay();
  const base = weekday === 0 ? 9300 : weekday === 6 ? 12100 : 46300;
  const wave = Math.round(Math.sin(index * 0.82) * 2400);
  const p50 = base + wave;
  return {
    date: date.toISOString().slice(0, 10),
    p10: Math.max(0, p50 - 4800),
    p50,
    p90: p50 + 6200,
  };
});

export const generatedObserved: ObservedDay[] = Array.from({ length: 14 }, (_, index) => {
  const date = new Date(Date.UTC(2026, 5, 17 + index));
  const weekday = date.getUTCDay();
  const base = weekday === 0 ? 9400 : weekday === 6 ? 11800 : 45500;
  return { date: date.toISOString().slice(0, 10), value: base + Math.round(Math.cos(index) * 2100) };
});

export const contextLanes = [
  {
    label: "Recorded appointments",
    value: "1.04m",
    detail: "Latest published month · not available capacity",
    tone: "observed",
  },
  {
    label: "Telephone",
    value: "71%",
    detail: "Calls answered · separate channel",
    tone: "telephone",
  },
  {
    label: "Online consultation",
    value: "92.4k",
    detail: "Submissions · never added to appointments",
    tone: "online",
  },
  {
    label: "Practice workforce",
    value: "4,182 FTE",
    detail: "Lagged context · not converted into capacity",
    tone: "workforce",
  },
  {
    label: "Registered population",
    value: "2.19m",
    detail: "July list size · denominator context",
    tone: "population",
  },
  {
    label: "Patient experience",
    value: "74%",
    detail: "2026 survey · explanatory context only",
    tone: "experience",
  },
  {
    label: "Deprivation",
    value: "Decile 4",
    detail: "Corrected IMD 2025 · not a forecast input",
    tone: "deprivation",
  },
  {
    label: "Respiratory surveillance",
    value: "Week 27",
    detail: "Lagged regional context · corrected release",
    tone: "respiratory",
  },
] as const;

const catalogueSeeds = [
  ["gpad-daily-june-2026", "GPAD daily", "Sub-ICB · day · status", "2026-06-30", "Analytical"],
  ["gpad-regional-june-2026", "GPAD regional", "Region · period · breakdown", "2026-06-30", "Analytical"],
  ["gpad-national-categories-june-2026", "GPAD national categories", "National · period · category", "2026-06-30", "Analytical"],
  ["gpad-sds-role-june-2026", "GPAD SDS role", "Published role grain", "2026-06-30", "Analytical"],
  ["gpad-actual-duration-june-2026", "GPAD duration", "Published duration grain", "2026-06-30", "Analytical"],
  ["gpad-national-overview-june-2026", "GPAD national overview", "National published cross-tab", "2026-06-30", "Reconciliation"],
  ["gpad-practice-level-june-2026", "GPAD practice level", "Practice · month · breakdown", "2026-06-30", "Analytical"],
  ["gpad-pcn-sub-icb-june-2026", "GPAD PCN and sub-ICB", "PCN/sub-ICB · month", "2026-06-30", "Analytical"],
  ["cloud-telephony-day-time-june-2026", "Telephony day and time", "Practice · day/time · measure", "2026-06-30", "Analytical"],
  ["cloud-telephony-durations-june-2026", "Telephony durations", "Practice · period · duration", "2026-06-30", "Analytical"],
  ["cloud-telephony-answered-june-2026", "Telephony answered calls", "Practice · period · outcome", "2026-06-30", "Analytical"],
  ["cloud-telephony-participation-june-2026", "Telephony participation", "Published participation grain", "2026-06-30", "Metadata"],
  ["online-consultation-june-2026", "Online consultation submissions", "Practice · month · submission", "2026-06-30", "Analytical"],
  ["online-consultation-day-time-june-2026", "Online consultation day and time", "Practice · day/time", "2026-06-30", "Analytical"],
  ["registered-patients-totals-july-2026", "Registered patient totals", "Practice · snapshot", "2026-07-01", "Analytical"],
  ["registered-patients-mapping-july-2026", "Registered patient mapping", "Practice · organisation", "2026-07-01", "Analytical"],
  ["registered-patients-age-bands-july-2026", "Registered patient age bands", "Practice · five-year age band", "2026-07-01", "Analytical"],
  ["registered-patients-lsoa-july-2026", "Registered patients by LSOA", "Practice · LSOA", "2026-07-01", "Analytical"],
  ["general-practice-workforce-june-2026", "Practice workforce", "Practice · staff group", "2026-06-30", "Analytical"],
  ["pcn-workforce-individual-june-2026", "PCN workforce", "PCN · published workforce row", "2026-06-30", "Analytical"],
  ["ods-epraccur-2026-08-12", "ODS practices", "Practice organisation snapshot", "2026-08-12", "Reference"],
  ["ods-epcn-2026-08-12", "ODS PCNs", "PCN organisation snapshot", "2026-08-12", "Reference"],
  ["gpps-national-2026", "GP Patient Survey national", "National · measure", "2026", "Context"],
  ["gpps-region-2026", "GP Patient Survey region", "Region · measure", "2026", "Context"],
  ["gpps-ics-2026", "GP Patient Survey ICS", "ICS · measure", "2026", "Context"],
  ["gpps-pcn-2026", "GP Patient Survey PCN", "PCN · measure", "2026", "Context"],
  ["gpps-practice-2026", "GP Patient Survey practice", "Practice · measure", "2026", "Context"],
  ["imd-2025-file-7-v2", "English deprivation indices", "LSOA · published measure", "2025 v2", "Context"],
  ["ukhsa-respiratory-week-27-2026", "Respiratory surveillance", "Published sheet row", "2026-W27", "Context"],
  ["govuk-bank-holidays-2026-08-12", "England and Wales bank holidays", "Holiday event", "2026-08-12", "Reference"],
] as const;

export const sourceCatalogue = catalogueSeeds.map(([id, label, grain, cutoff, className]) => ({
  id,
  label,
  grain,
  cutoff,
  className,
  coverage: className === "Analytical" ? "Publisher coverage retained per source row." : "Used as published context, reference, or reconciliation.",
  fields: className === "Analytical" ? "Field names and publisher null/suppression values are preserved in bounded pages." : "Definitions follow the linked publisher metadata retained in the release.",
}));

export const generatedSourcePage = [
  {
    SUB_ICB_LOCATION_CODE: "00L",
    Appointment_Date: "01JUN2026",
    APPT_STATUS: "Attended",
    HCP_TYPE: "GP",
    APPT_MODE: "Face-to-Face",
    COUNT_OF_APPOINTMENTS: "1842",
  },
  {
    SUB_ICB_LOCATION_CODE: "00L",
    Appointment_Date: "01JUN2026",
    APPT_STATUS: "DNA",
    HCP_TYPE: "GP",
    APPT_MODE: "Face-to-Face",
    COUNT_OF_APPOINTMENTS: "91",
  },
] as const;

export const isFixtureMode = process.env.NEXT_PUBLIC_FIXTURE_MODE === "true";
