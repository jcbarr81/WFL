from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conference, Contract, Division, League, Player, Team

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

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
            "conference",
            "division",
            "league",
        ]
        read_only_fields = ["league"]

    def validate(self, attrs):
        league = attrs.get("league") or self.context.get("league")
        conference = attrs.get("conference")
        division = attrs.get("division")

        errors = {}
        if conference and conference.league_id != league.id:
            errors["conference"] = "Conference must belong to the same league."
        if division and division.conference_id != getattr(conference, "id", None):
            errors["division"] = "Division must belong to the conference."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        league = self.context.get("league") or validated_data.get("league")
        validated_data["league"] = league
        return super().create(validated_data)


class DivisionSerializer(serializers.ModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)

    class Meta:
        model = Division
        fields = ["id", "name", "order", "teams"]


class ConferenceSerializer(serializers.ModelSerializer):
    divisions = DivisionSerializer(many=True, read_only=True)

    class Meta:
        model = Conference
        fields = ["id", "name", "order", "divisions"]


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
            "team",
        ]
        read_only_fields = ["team"]


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
