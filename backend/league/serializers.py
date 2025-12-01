from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Conference,
    Contract,
    Division,
    Game,
    League,
    Player,
    Season,
    Team,
    Trade,
    TradeItem,
    Draft,
    DraftPick,
    WaiverClaim,
    Week,
    Injury,
    FreeAgencyBid,
    Notification,
)

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner_email_input = serializers.EmailField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "city",
            "nickname",
            "abbreviation",
            "primary_color",
            "secondary_color",
            "owner",
            "owner_email",
            "owner_email_input",
            "conference",
            "division",
            "league",
            "stadium_name",
            "stadium_capacity",
            "stadium_turf",
            "stadium_weather",
        ]
        read_only_fields = ["league"]

    def validate(self, attrs):
        league = attrs.get("league") or self.context.get("league")
        conference = attrs.get("conference")
        division = attrs.get("division")
        owner_email_input = attrs.pop("owner_email_input", "").strip().lower() if "owner_email_input" in attrs else ""
        owner = attrs.get("owner")

        errors = {}
        if conference and conference.league_id != league.id:
            errors["conference"] = "Conference must belong to the same league."
        if division and division.conference_id != getattr(conference, "id", None):
            errors["division"] = "Division must belong to the conference."
        if owner_email_input:
            try:
                owner = User.objects.get(email__iexact=owner_email_input)
                attrs["owner"] = owner
            except User.DoesNotExist:
                errors["owner_email_input"] = "Owner email not found."
        if attrs.get("stadium_capacity") is not None and attrs["stadium_capacity"] <= 0:
            errors["stadium_capacity"] = "Stadium capacity must be greater than zero."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        league = self.context.get("league") or validated_data.get("league")
        validated_data["league"] = league
        if "owner" not in validated_data and self.context.get("request"):
            validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class DivisionSerializer(serializers.ModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)

    class Meta:
        model = Division
        fields = ["id", "name", "order", "teams"]


class DivisionRenameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ["id", "name"]
        read_only_fields = ["id"]


class ConferenceSerializer(serializers.ModelSerializer):
    divisions = DivisionSerializer(many=True, read_only=True)

    class Meta:
        model = Conference
        fields = ["id", "name", "order", "divisions"]


class ConferenceRenameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conference
        fields = ["id", "name"]
        read_only_fields = ["id"]


class LeagueStructureSerializer(serializers.ModelSerializer):
    conferences = ConferenceSerializer(many=True, read_only=True)

    class Meta:
        model = League
        fields = [
            "id",
            "name",
            "conference_count",
            "division_count_per_conference",
            "teams_per_division",
            "salary_cap",
            "roster_size_limit",
            "conferences",
        ]


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = [
            "id",
            "first_name",
            "last_name",
            "position",
            "age",
            "height_inches",
            "weight_lbs",
            "overall_rating",
            "potential_rating",
            "injury_status",
            "league",
            "team",
            "is_rookie_pool",
        ]
        read_only_fields = ["team", "is_rookie_pool", "league"]


class ContractSerializer(serializers.ModelSerializer):
    cap_hit = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Contract
        fields = ["id", "player", "team", "salary", "bonus", "years", "start_year", "cap_hit"]
        read_only_fields = ["team", "cap_hit"]
        extra_kwargs = {"player": {"required": False}}

    def validate(self, attrs):
        team = attrs.get("team") or self.context.get("team")
        if team is None:
            raise serializers.ValidationError("Team is required.")
        attrs["team"] = team
        league = team.league

        # Cap check
        current_cap = sum(c.cap_hit for c in team.contracts.all())
        new_cap_hit = (attrs.get("salary") or 0) + (attrs.get("bonus") or 0)
        if current_cap + new_cap_hit > league.salary_cap:
            raise serializers.ValidationError({"salary": "Cap exceeded for this team."})

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["cap_hit"] = instance.cap_hit
        return data


class RosterPlayerSerializer(serializers.Serializer):
    player = PlayerSerializer()
    contract = ContractSerializer()


class LeagueSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = League
        fields = [
            "id",
            "name",
            "created_by",
            "created_by_email",
            "conference_count",
            "division_count_per_conference",
            "teams_per_division",
            "salary_cap",
            "roster_size_limit",
            "free_agency_mode",
            "allow_cap_growth",
            "allow_playoff_expansion",
            "enable_realignment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        league = League.objects.create(created_by=user, **validated_data)

        # Create conferences/divisions scaffold for immediate use
        for conf_index in range(league.conference_count):
            conf = Conference.objects.create(
                league=league, name=f"Conference {conf_index + 1}", order=conf_index
            )
            for div_index in range(league.division_count_per_conference):
                Division.objects.create(
                    conference=conf,
                    name=f"Division {div_index + 1}",
                    order=div_index,
                )
        return league


class GameSerializer(serializers.ModelSerializer):
    home_team_abbr = serializers.CharField(source="home_team.abbreviation", read_only=True)
    away_team_abbr = serializers.CharField(source="away_team.abbreviation", read_only=True)

    class Meta:
        model = Game
        fields = [
            "id",
            "week",
            "home_team",
            "away_team",
            "home_team_abbr",
            "away_team_abbr",
            "home_score",
            "away_score",
            "status",
            "scheduled_at",
            "winner",
            "loser",
        ]
        read_only_fields = ["status", "scheduled_at", "week", "winner", "loser"]


class WeekSerializer(serializers.ModelSerializer):
    games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = ["id", "number", "is_playoffs", "games"]


class SeasonSerializer(serializers.ModelSerializer):
    weeks = WeekSerializer(many=True, read_only=True)

    class Meta:
        model = Season
        fields = ["id", "year", "weeks"]


class TradeItemSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.__str__", read_only=True)

    class Meta:
        model = TradeItem
        fields = ["id", "player", "from_team", "to_team", "player_name"]
        read_only_fields = ["from_team", "to_team"]


class TradeSerializer(serializers.ModelSerializer):
    items = TradeItemSerializer(many=True, write_only=True)
    items_detail = TradeItemSerializer(many=True, source="items", read_only=True)
    from_team_abbr = serializers.CharField(source="from_team.abbreviation", read_only=True)
    to_team_abbr = serializers.CharField(source="to_team.abbreviation", read_only=True)

    class Meta:
        model = Trade
        fields = [
            "id",
            "league",
            "from_team",
            "to_team",
            "from_team_abbr",
            "to_team_abbr",
            "status",
            "items",
            "items_detail",
            "created_at",
        ]
        read_only_fields = ["status", "created_at", "league"]

    def validate(self, attrs):
        from_team = attrs.get("from_team")
        to_team = attrs.get("to_team")
        if from_team == to_team:
            raise serializers.ValidationError("from_team and to_team must differ.")
        league = self.context.get("league")
        if from_team.league_id != league.id or to_team.league_id != league.id:
            raise serializers.ValidationError("Teams must belong to this league.")
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        league = self.context.get("league")
        validated_data["league"] = league
        trade = Trade.objects.create(**validated_data)
        for item in items_data:
            player = item["player"]
            from_team = item.get("from_team") or player.team
            if player.team_id != from_team.id:
                raise serializers.ValidationError({"items": f"Player {player.id} does not belong to from_team."})
            to_team = item.get("to_team") or (
                trade.to_team if player.team_id == trade.from_team_id else trade.from_team
            )
            TradeItem.objects.create(
                trade=trade,
                player=player,
                from_team=from_team,
                to_team=to_team,
            )
        return trade


class WaiverClaimSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.__str__", read_only=True)
    from_team_abbr = serializers.CharField(source="from_team.abbreviation", read_only=True)
    claimed_by_abbr = serializers.CharField(source="claimed_by.abbreviation", read_only=True)

    class Meta:
        model = WaiverClaim
        fields = [
            "id",
            "league",
            "player",
            "player_name",
            "from_team",
            "from_team_abbr",
            "claimed_by",
            "claimed_by_abbr",
            "status",
            "created_at",
            "awarded_at",
        ]
        read_only_fields = ["league", "status", "awarded_at", "claimed_by"]


class DraftPickSerializer(serializers.ModelSerializer):
    team_abbr = serializers.CharField(source="team.abbreviation", read_only=True)
    player_name = serializers.CharField(source="player.__str__", read_only=True)

    class Meta:
        model = DraftPick
        fields = [
            "id",
            "round_number",
            "overall_number",
            "team",
            "team_abbr",
            "player",
            "player_name",
            "is_selected",
            "selected_at",
        ]
        read_only_fields = ["round_number", "overall_number", "team", "is_selected", "selected_at"]


class DraftSerializer(serializers.ModelSerializer):
    picks = DraftPickSerializer(many=True, read_only=True)

    class Meta:
        model = Draft
        fields = ["id", "league", "season", "draft_type", "rounds", "is_complete", "picks", "created_at"]
        read_only_fields = ["is_complete", "picks", "created_at", "league"]


class StandingSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    abbreviation = serializers.CharField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    points_for = serializers.IntegerField()
    points_against = serializers.IntegerField()
    conference = serializers.CharField()
    division = serializers.CharField()


class PlayoffSeedSerializer(StandingSerializer):
    seed = serializers.IntegerField()


class PlayoffMatchupSerializer(serializers.Serializer):
    higher_seed = PlayoffSeedSerializer()
    lower_seed = PlayoffSeedSerializer(allow_null=True)


class InjurySerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.__str__", read_only=True)

    class Meta:
        model = Injury
        fields = [
            "id",
            "player",
            "player_name",
            "league",
            "severity",
            "duration_weeks",
            "status",
            "created_at",
            "resolved_at",
        ]
        read_only_fields = ["league", "status", "created_at", "resolved_at", "player_name"]


class FreeAgencyBidSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.__str__", read_only=True)
    team_abbr = serializers.CharField(source="team.abbreviation", read_only=True)

    class Meta:
        model = FreeAgencyBid
        fields = [
            "id",
            "league",
            "player",
            "player_name",
            "team",
            "team_abbr",
            "amount",
            "mode",
            "round_number",
            "expires_at",
            "status",
            "created_at",
            "awarded_at",
        ]
        read_only_fields = [
            "league",
            "status",
            "created_at",
            "awarded_at",
            "player_name",
            "team_abbr",
            "mode",
            "round_number",
            "expires_at",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]
        read_only_fields = ["message", "created_at"]
