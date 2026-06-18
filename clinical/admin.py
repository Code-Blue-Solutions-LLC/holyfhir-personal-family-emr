from django.contrib import admin
from .models import (
    Allergy,
    CareTeam,
    Condition,
    Encounter,
    Immunization,
    Location,
    Medication,
    Observation,
    Organization,
    Practitioner,
)


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "clinical_status", "onset_date")
    search_fields = ("name", "icd10_code", "snomed_code")
    list_filter = ("patient", "clinical_status")
    autocomplete_fields = ["patient"]
    ordering = ("-onset_date",)


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "substance", "category", "severity")
    search_fields = ("substance", "rxnorm_code", "snomed_code")
    list_filter = ("patient", "category", "severity", "criticality")
    autocomplete_fields = ["patient"]


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "status", "indication", "start_date")
    search_fields = ("name", "rxnorm_code", "prescriber")
    list_filter = ("patient", "status")
    ordering = ("-start_date",)
    autocomplete_fields = ["patient"]


@admin.register(Immunization)
class ImmunizationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "vaccine_name", "occurrence_date")
    search_fields = ("vaccine_name", "cvx_code")
    list_filter = ("patient",)
    ordering = ("-occurrence_date",)
    autocomplete_fields = ["patient"]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "category", "effective_datetime")
    search_fields = ("name", "loinc_code")
    list_filter = ("patient", "category")
    ordering = ("-effective_datetime",)
    autocomplete_fields = ["patient"]


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "encounter_type", "provider_name", "facility_name", "start_time")
    search_fields = ("provider_name", "facility_name", "reason")
    list_filter = ("patient", "status")
    ordering = ("-start_time",)
    autocomplete_fields = ["patient"]


@admin.register(CareTeam)
class CareTeamAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "name", "status", "category", "start_date")
    search_fields = ("name", "category", "participants", "reason")
    list_filter = ("patient", "status", "category")
    ordering = ("patient", "name")
    autocomplete_fields = ["patient"]


@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "qualification", "phone", "email", "active")
    search_fields = ("name", "npi", "qualification", "phone", "email")
    list_filter = ("active", "qualification")
    ordering = ("name",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization_type", "phone", "email", "active")
    search_fields = ("name", "organization_type", "phone", "email")
    list_filter = ("active", "organization_type")
    ordering = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "mode", "location_type", "managing_organization")
    search_fields = ("name", "location_type", "managing_organization", "phone", "email")
    list_filter = ("status", "mode", "location_type")
    ordering = ("name",)
