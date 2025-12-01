from django.contrib import admin

from .models import (
    AuditLog,
    Conference,
    Contract,
    Draft,
    DraftPick,
    Division,
    Game,
    League,
    Player,
    Season,
    Team,
    Trade,
    TradeItem,
    WaiverClaim,
    Week,
)


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "conference_count", "division_count_per_conference", "teams_per_division")
    search_fields = ("name", "created_by__email")
    list_filter = ("free_agency_mode", "allow_cap_growth", "allow_playoff_expansion")


@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "order")
    list_filter = ("league",)


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("name", "conference", "order")
    list_filter = ("conference",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("abbreviation", "name", "league", "conference", "division", "owner")
    search_fields = ("name", "city", "nickname", "abbreviation", "owner__email")
    list_filter = ("league", "conference", "division")


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("league", "year")
    list_filter = ("league",)


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ("season", "number", "is_playoffs")
    list_filter = ("season__league", "is_playoffs")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("week", "home_team", "away_team", "status", "scheduled_at")
    list_filter = ("status", "week__season__league")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "position", "team", "overall_rating")
    search_fields = ("first_name", "last_name", "team__name", "team__abbreviation")
    list_filter = ("position",)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("player", "team", "salary", "bonus", "years", "start_year")
    list_filter = ("team", "start_year")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "user", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_id", "user__email")


class TradeItemInline(admin.TabularInline):
    model = TradeItem
    extra = 0


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("id", "league", "from_team", "to_team", "status", "created_by", "created_at")
    list_filter = ("league", "status")
    inlines = [TradeItemInline]


@admin.register(WaiverClaim)
class WaiverClaimAdmin(admin.ModelAdmin):
    list_display = ("player", "league", "from_team", "status", "claimed_by", "created_at")
    list_filter = ("league", "status")


class DraftPickInline(admin.TabularInline):
    model = DraftPick
    extra = 0


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ("league", "draft_type", "rounds", "is_complete", "created_at")
    list_filter = ("league", "draft_type", "is_complete")
    inlines = [DraftPickInline]
