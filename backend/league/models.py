from django.conf import settings
from django.db import models
from django.utils import timezone


class League(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leagues_created"
    )
    conference_count = models.PositiveIntegerField(default=2)
    division_count_per_conference = models.PositiveIntegerField(default=4)
    teams_per_division = models.PositiveIntegerField(default=4)
    free_agency_mode = models.CharField(
        max_length=20,
        choices=[("auction", "Auction"), ("rounds", "RoundBased")],
        default="auction",
    )
    salary_cap = models.DecimalField(max_digits=12, decimal_places=2, default=200000000.00)
    roster_size_limit = models.PositiveIntegerField(default=53)
    allow_cap_growth = models.BooleanField(default=False)
    allow_playoff_expansion = models.BooleanField(default=False)
    enable_realignment = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Conference(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="conferences")
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("league", "name")
        ordering = ["order"]

    def __str__(self):
        return f"{self.league.name} - {self.name}"


class Division(models.Model):
    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name="divisions"
    )
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("conference", "name")
        ordering = ["order"]

    def __str__(self):
        return f"{self.conference.name} - {self.name}"


class Team(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="teams")
    conference = models.ForeignKey(Conference, on_delete=models.PROTECT, related_name="teams")
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name="teams")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams_owned",
    )
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=5)
    primary_color = models.CharField(max_length=7, default="#000000")
    secondary_color = models.CharField(max_length=7, default="#FFFFFF")
    stadium_name = models.CharField(max_length=255, blank=True, default="")
    stadium_capacity = models.PositiveIntegerField(default=60000)
    stadium_turf = models.CharField(
        max_length=20,
        choices=[("grass", "Grass"), ("turf", "Turf"), ("hybrid", "Hybrid")],
        default="grass",
    )
    stadium_weather = models.CharField(
        max_length=20,
        choices=[("temperate", "Temperate"), ("cold", "Cold"), ("dome", "Dome"), ("extreme", "Extreme")],
        default="temperate",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("league", "abbreviation")
        ordering = ["league_id", "abbreviation"]

    def __str__(self):
        return f"{self.city} {self.nickname}"


class Season(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="seasons")
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("league", "year")

    def __str__(self):
        return f"{self.league.name} {self.year}"


class Week(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="weeks")
    number = models.PositiveIntegerField()
    is_playoffs = models.BooleanField(default=False)

    class Meta:
        unique_together = ("season", "number", "is_playoffs")
        ordering = ["season_id", "number"]

    def __str__(self):
        label = "Playoffs" if self.is_playoffs else "Regular"
        return f"{self.season} Week {self.number} ({label})"


class Game(models.Model):
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="games")
    home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_games")
    away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_games")
    home_score = models.IntegerField(default=0)
    away_score = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[("scheduled", "Scheduled"), ("completed", "Completed"), ("in_progress", "In Progress")],
        default="scheduled",
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    winner = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="wins")
    loser = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="losses")

    class Meta:
        ordering = ["week_id", "id"]

    def __str__(self):
        return f"{self.away_team} at {self.home_team} ({self.week})"


class Player(models.Model):
    POSITION_CHOICES = [
        ("QB", "Quarterback"),
        ("RB", "Running Back"),
        ("WR", "Wide Receiver"),
        ("TE", "Tight End"),
        ("OL", "Offensive Line"),
        ("DL", "Defensive Line"),
        ("LB", "Linebacker"),
        ("CB", "Cornerback"),
        ("S", "Safety"),
        ("K", "Kicker"),
        ("P", "Punter"),
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    position = models.CharField(max_length=3, choices=POSITION_CHOICES)
    age = models.PositiveIntegerField(default=21)
    height_inches = models.PositiveIntegerField(default=72)
    weight_lbs = models.PositiveIntegerField(default=200)
    overall_rating = models.PositiveIntegerField(default=60)
    potential_rating = models.PositiveIntegerField(default=70)
    injury_status = models.CharField(max_length=50, default="healthy")
    league = models.ForeignKey(League, null=True, blank=True, on_delete=models.CASCADE, related_name="players")
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="players")
    is_rookie_pool = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"


class Injury(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("resolved", "Resolved"),
    ]

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="injuries")
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="injuries")
    severity = models.CharField(max_length=50, default="minor")
    duration_weeks = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player} - {self.severity} ({self.status})"


class Contract(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="contract")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="contracts")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    years = models.PositiveIntegerField(default=1)
    start_year = models.PositiveIntegerField(default=2025)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["team_id", "player_id"]

    @property
    def cap_hit(self):
        return self.salary + self.bonus

    def __str__(self):
        return f"{self.player} - {self.team} (${self.salary} + ${self.bonus})"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("league.create", "League Created"),
        ("league.update", "League Updated"),
        ("league.delete", "League Deleted"),
        ("team.create", "Team Created"),
        ("team.delete", "Team Deleted"),
        ("roster.add", "Roster Add"),
        ("roster.release", "Roster Release"),
        ("league.schedule.generate", "Schedule Generated"),
        ("trade.create", "Trade Created"),
        ("trade.accept", "Trade Accepted"),
        ("trade.reverse", "Trade Reversed"),
        ("waiver.release", "Waiver Release"),
        ("waiver.claim", "Waiver Claim"),
        ("fa.bid", "Free Agency Bid"),
        ("fa.award", "Free Agency Award"),
        ("contract.update", "Contract Update"),
        ("draft.create", "Draft Created"),
        ("draft.pick", "Draft Pick Made"),
        ("game.complete", "Game Completed"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.entity_type} {self.entity_id}"


class Trade(models.Model):
    STATUS_CHOICES = [
        ("proposed", "Proposed"),
        ("accepted", "Accepted"),
        ("reversed", "Reversed"),
        ("rejected", "Rejected"),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="trades")
    from_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="trades_out")
    to_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="trades_in")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="proposed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Trade {self.id} {self.from_team} -> {self.to_team} ({self.status})"


class FreeAgencyBid(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("awarded", "Awarded"),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="fa_bids")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="fa_bids")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="fa_bids")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mode = models.CharField(max_length=20, default="auction")
    round_number = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    awarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"FA Bid {self.player} -> {self.team} (${self.amount}) [{self.status}]"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.message}"


class TradeItem(models.Model):
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="items")
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    from_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="trade_items_from")
    to_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="trade_items_to")

    class Meta:
        unique_together = ("trade", "player")

    def __str__(self):
        return f"{self.player} {self.from_team} -> {self.to_team}"


class Draft(models.Model):
    TYPE_CHOICES = [
        ("rookie", "Rookie"),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="drafts")
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="drafts", null=True, blank=True)
    draft_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="rookie")
    rounds = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.league.name} {self.get_draft_type_display()} Draft"


class DraftPick(models.Model):
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name="picks")
    round_number = models.PositiveIntegerField()
    overall_number = models.PositiveIntegerField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="draft_picks")
    player = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL, related_name="draft_pick")
    original_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="original_picks")
    is_selected = models.BooleanField(default=False)
    selected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["overall_number"]
        unique_together = ("draft", "overall_number")

    def __str__(self):
        return f"Pick {self.overall_number} (Round {self.round_number})"


class WaiverClaim(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("awarded", "Awarded"),
        ("failed", "Failed"),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="waiver_claims")
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="waiver_claim")
    from_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name="waivers_out")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    claimed_by = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="waivers_in")
    created_at = models.DateTimeField(auto_now_add=True)
    awarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Waiver {self.player} ({self.status})"
