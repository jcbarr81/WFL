from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import (
    Draft,
    DraftPick,
    FreeAgencyBid,
    Game,
    Injury,
    League,
    Notification,
    Player,
    Season,
    Team,
    Trade,
    TradeItem,
    WaiverClaim,
    Week,
    Conference,
    Division,
    Contract,
)
from .serializers import (
    ContractSerializer,
    DraftSerializer,
    DraftPickSerializer,
    GameSerializer,
    LeagueSerializer,
    LeagueStructureSerializer,
    ConferenceRenameSerializer,
    PlayerSerializer,
    DivisionRenameSerializer,
    PlayoffSeedSerializer,
    PlayoffMatchupSerializer,
    SeasonSerializer,
    TradeSerializer,
    WaiverClaimSerializer,
    TeamSerializer,
    StandingSerializer,
    InjurySerializer,
    FreeAgencyBidSerializer,
    NotificationSerializer,
)
from .services.schedule_generator import generate_regular_season_schedule
from .services.standings import compute_standings
from .services.playoffs import generate_playoff_seeds, generate_bracket
from .utils import log_action


class LeagueListCreateView(generics.ListCreateAPIView):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return League.objects.filter(created_by=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        league = serializer.save()
        log_action(
            user=self.request.user,
            action="league.create",
            entity_type="league",
            entity_id=league.id,
            details={"league_id": league.id, "name": league.name},
            request=self.request,
        )


class LeagueDetailView(generics.RetrieveAPIView):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = League.objects.all()




class LeagueDeleteView(generics.DestroyAPIView):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = League.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or instance.created_by_id == user.id
        ):
            return Response({"detail": "Not authorized to delete league."}, status=status.HTTP_403_FORBIDDEN)
        league_id = instance.id
        from .models import Game, Team

        Game.objects.filter(week__season__league=instance).delete()
        Team.objects.filter(league=instance).delete()
        response = super().destroy(request, *args, **kwargs)
        log_action(
            user=user,
            action="league.delete",
            entity_type="league",
            entity_id=league_id,
            details={"league_id": league_id},
            request=request,
        )
        return response
class LeagueUpdateView(generics.UpdateAPIView):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = League.objects.all()

    def update(self, request, *args, **kwargs):
        league = self.get_object()
        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or league.created_by_id == user.id
        ):
            return Response({"detail": "Not authorized to update league."}, status=status.HTTP_403_FORBIDDEN)

        partial = kwargs.pop("partial", True)
        serializer = self.get_serializer(league, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(
            user=user,
            action="league.update",
            entity_type="league",
            entity_id=league.id,
            details={"league_id": league.id, "fields": list(request.data.keys())},
            request=request,
        )
        return Response(serializer.data)


class LeagueStructureView(generics.RetrieveAPIView):
    serializer_class = LeagueStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = League.objects.all()


class ConferenceRenameView(generics.UpdateAPIView):
    serializer_class = ConferenceRenameSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conference.objects.all()
    lookup_url_kwarg = "conf_id"

    def update(self, request, *args, **kwargs):
        conference = self.get_object()
        user = request.user
        league = conference.league
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or league.created_by_id == user.id
        ):
            return Response({"detail": "Not authorized to rename conference."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class DivisionRenameView(generics.UpdateAPIView):
    serializer_class = DivisionRenameSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Division.objects.all()
    lookup_url_kwarg = "div_id"

    def update(self, request, *args, **kwargs):
        division = self.get_object()
        user = request.user
        conference = division.conference
        league = conference.league
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or league.created_by_id == user.id
        ):
            return Response({"detail": "Not authorized to rename division."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class TeamCreateView(generics.CreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        context["league"] = league
        return context

    def perform_create(self, serializer):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        owner = serializer.validated_data.get("owner") or self.request.user
        team = serializer.save(league=league, owner=owner)
        log_action(
            user=self.request.user,
            action="team.create",
            entity_type="team",
            entity_id=team.id,
            details={"league_id": league.id, "team": serializer.data},
            request=self.request,
        )


class TeamListView(generics.ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return league.teams.select_related("conference", "division", "owner").order_by("abbreviation")


class TeamRosterView(generics.ListAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        team_id = self.kwargs.get("team_id")
        league = generics.get_object_or_404(League, pk=league_id)
        team = generics.get_object_or_404(league.teams, pk=team_id)
        return Player.objects.filter(team=team).order_by("position", "last_name")


class TeamRosterCreateView(generics.CreateAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        team = self._get_team()
        context["team"] = team
        return context

    def _get_team(self):
        league_id = self.kwargs.get("league_id")
        team_id = self.kwargs.get("team_id")
        league = generics.get_object_or_404(League, pk=league_id)
        team = generics.get_object_or_404(league.teams, pk=team_id)
        return team

    def create(self, request, *args, **kwargs):
        team = self._get_team()
        league = team.league

        if team.players.count() >= league.roster_size_limit:
            return Response({"detail": "Roster limit reached."}, status=status.HTTP_400_BAD_REQUEST)

        player_serializer = self.get_serializer(data=request.data)
        player_serializer.is_valid(raise_exception=True)
        player = player_serializer.save(team=team)

        # Optional contract data
        contract_data = request.data.get("contract")
        if contract_data:
            from .serializers import ContractSerializer

            contract_serializer = ContractSerializer(
                data=contract_data, context={"team": team}
            )
            contract_serializer.is_valid(raise_exception=True)
            contract_serializer.save(player=player, team=team)

        headers = self.get_success_headers(player_serializer.data)
        log_action(
            user=request.user,
            action="roster.add",
            entity_type="player",
            entity_id=player.id,
            details={"team_id": team.id, "league_id": league.id},
            request=request,
        )
        return Response(player_serializer.data, status=status.HTTP_201_CREATED, headers=headers)




class TeamDeleteView(generics.DestroyAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Team.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "team_id"

    def get_queryset(self):
        qs = super().get_queryset()
        league_id = self.kwargs.get("league_id")
        if league_id:
            qs = qs.filter(league_id=league_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        league = team.league
        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or league.created_by_id == user.id
            or team.owner_id == user.id
        ):
            return Response({"detail": "Not authorized to delete team."}, status=status.HTTP_403_FORBIDDEN)
        team_id = team.id
        league_id = league.id
        from .models import Game

        Game.objects.filter(week__season__league=league, home_team=team).delete()
        Game.objects.filter(week__season__league=league, away_team=team).delete()
        response = super().destroy(request, *args, **kwargs)
        log_action(
            user=user,
            action="team.delete",
            entity_type="team",
            entity_id=team_id,
            details={"team_id": team_id, "league_id": league_id},
            request=request,
        )
        return response
class TeamRosterReleaseView(generics.DestroyAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        league_id = self.kwargs.get("league_id")
        team_id = self.kwargs.get("team_id")
        player_id = self.kwargs.get("player_id")
        league = generics.get_object_or_404(League, pk=league_id)
        team = generics.get_object_or_404(league.teams, pk=team_id)
        player = generics.get_object_or_404(Player, pk=player_id, team=team)
        return player

    def perform_destroy(self, instance):
        team = instance.team
        league = team.league
        # Remove contract if exists
        if hasattr(instance, "contract"):
            instance.contract.delete()
        instance.team = None
        instance.save(update_fields=["team"])
        log_action(
            user=self.request.user,
            action="roster.release",
            entity_type="player",
            entity_id=instance.id,
            details={"team_id": team.id, "league_id": league.id},
            request=self.request,
        )


class SeasonGenerateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, league_id):
        league = generics.get_object_or_404(League, pk=league_id)
        year = request.data.get("year")
        if year is None:
            return Response({"detail": "year is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            season = generate_regular_season_schedule(league, int(year))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        log_action(
            user=request.user,
            action="league.schedule.generate",
            entity_type="season",
            entity_id=season.id,
            details={"league_id": league.id, "year": year},
            request=request,
        )
        return Response({"season_id": season.id, "year": season.year}, status=status.HTTP_201_CREATED)


class SeasonScheduleView(generics.RetrieveAPIView):
    serializer_class = SeasonSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "year"
    lookup_url_kwarg = "year"

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return Season.objects.filter(league=league)


class TradeListCreateView(generics.ListCreateAPIView):
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return Trade.objects.filter(league=league).select_related("from_team", "to_team").prefetch_related("items")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        context["league"] = league
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        league = self.get_serializer_context()["league"]
        user = request.user
        from_team = serializer.validated_data["from_team"]
        to_team = serializer.validated_data["to_team"]
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or from_team.owner_id == user.id
            or to_team.owner_id == user.id
        ):
            return Response({"detail": "Not authorized to create this trade."}, status=status.HTTP_403_FORBIDDEN)

        trade = serializer.save(created_by=user)
        log_action(
            user=user,
            action="trade.create",
            entity_type="trade",
            entity_id=trade.id,
            details={"league_id": league.id, "status": trade.status},
            request=request,
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TradeAcceptView(generics.UpdateAPIView):
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Trade.objects.all()

    def update(self, request, *args, **kwargs):
        trade = self.get_object()
        if trade.status != "proposed":
            return Response({"detail": "Trade is not in proposed state."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or trade.from_team.owner_id == user.id
            or trade.to_team.owner_id == user.id
        ):
            return Response({"detail": "Not authorized to accept this trade."}, status=status.HTTP_403_FORBIDDEN)

        # Apply moves
        roster_limits_error = self._check_roster_and_cap(trade)
        if roster_limits_error:
            return Response(roster_limits_error, status=status.HTTP_400_BAD_REQUEST)

        for item in trade.items.select_related("player"):
            player = item.player
            player.team = item.to_team
            player.save(update_fields=["team"])

        trade.status = "accepted"
        trade.save(update_fields=["status"])
        log_action(
            user=request.user,
            action="trade.accept",
            entity_type="trade",
            entity_id=trade.id,
            details={"league_id": trade.league_id},
            request=request,
        )
        serializer = self.get_serializer(trade)
        return Response(serializer.data)

    def _check_roster_and_cap(self, trade: Trade):
        league = trade.league
        limits = {}
        for team in [trade.from_team, trade.to_team]:
            limits[team.id] = {
                "count": team.players.count(),
                "cap": sum(c.cap_hit for c in team.contracts.all()),
            }
        for item in trade.items.select_related("player"):
            from_team = item.from_team
            to_team = item.to_team
            limits[from_team.id]["count"] -= 1
            limits[to_team.id]["count"] += 1
            if hasattr(item.player, "contract"):
                cap_hit = item.player.contract.cap_hit
                limits[from_team.id]["cap"] -= cap_hit
                limits[to_team.id]["cap"] += cap_hit

        errors = {}
        for team in [trade.from_team, trade.to_team]:
            count = limits[team.id]["count"]
            if count > league.roster_size_limit:
                errors["roster"] = f"Team {team.abbreviation} exceeds roster limit."
            cap = limits[team.id]["cap"]
            if cap > league.salary_cap:
                errors["cap"] = f"Team {team.abbreviation} exceeds salary cap."
        return errors if errors else None


class TradeReverseView(generics.UpdateAPIView):
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Trade.objects.all()

    def update(self, request, *args, **kwargs):
        trade = self.get_object()
        if trade.status != "accepted":
            return Response({"detail": "Only accepted trades can be reversed."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not (getattr(user, "is_commissioner", False) or user.is_staff or user.is_superuser):
            return Response({"detail": "Not authorized to reverse trades."}, status=status.HTTP_403_FORBIDDEN)

        for item in trade.items.select_related("player"):
            player = item.player
            player.team = item.from_team
            player.save(update_fields=["team"])

        trade.status = "reversed"
        trade.save(update_fields=["status"])
        log_action(
            user=request.user,
            action="trade.reverse",
            entity_type="trade",
            entity_id=trade.id,
            details={"league_id": trade.league_id},
            request=request,
        )
        serializer = self.get_serializer(trade)
        return Response(serializer.data)


class WaiverReleaseView(generics.CreateAPIView):
    serializer_class = WaiverClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        player_id = request.data.get("player_id")
        team_id = request.data.get("team_id")
        player = generics.get_object_or_404(Player, pk=player_id, team__league=league)
        team = generics.get_object_or_404(Team, pk=team_id, league=league)

        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or team.owner_id == user.id
        ):
            return Response({"detail": "Not authorized to release this player."}, status=status.HTTP_403_FORBIDDEN)

        player.team = None
        player.save(update_fields=["team"])

        claim = WaiverClaim.objects.create(league=league, player=player, from_team=team)
        log_action(
            user=request.user,
            action="waiver.release",
            entity_type="player",
            entity_id=player.id,
            details={"league_id": league.id, "from_team": team.id, "claim_id": claim.id},
            request=request,
        )
        serializer = self.get_serializer(claim)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WaiverListView(generics.ListAPIView):
    serializer_class = WaiverClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return WaiverClaim.objects.filter(league=league).select_related("player", "from_team", "claimed_by")


class WaiverClaimView(generics.UpdateAPIView):
    serializer_class = WaiverClaimSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WaiverClaim.objects.all()

    def update(self, request, *args, **kwargs):
        claim = self.get_object()
        if claim.status != "pending":
            return Response({"detail": "Waiver is not pending."}, status=status.HTTP_400_BAD_REQUEST)
        team_id = request.data.get("team_id")
        team = generics.get_object_or_404(Team, pk=team_id, league=claim.league)

        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or team.owner_id == user.id
        ):
            return Response({"detail": "Not authorized to claim for this team."}, status=status.HTTP_403_FORBIDDEN)

        player = claim.player
        player.team = team
        player.save(update_fields=["team"])

        claim.status = "awarded"
        claim.claimed_by = team
        claim.awarded_at = timezone.now()
        claim.save(update_fields=["status", "claimed_by", "awarded_at"])

        log_action(
            user=request.user,
            action="waiver.claim",
            entity_type="waiver",
            entity_id=claim.id,
            details={"league_id": claim.league_id, "player_id": player.id, "team_id": team.id},
            request=request,
        )
        serializer = self.get_serializer(claim)
        return Response(serializer.data)


class RookiePoolGenerateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, league_id):
        league = generics.get_object_or_404(League, pk=league_id)
        # simple deterministic pool
        import random
        first_names = ["Alex", "Jordan", "Chris", "Taylor", "Casey", "Sam", "Devin", "Riley", "Quinn", "Shawn"]
        last_names = ["Johnson", "Miller", "Davis", "Thompson", "Lewis", "Walker", "Robinson", "Young", "Allen", "Parker"]
        positions = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "K", "P"]
        created = []
        for i in range(30):
            first = random.choice(first_names)
            last = random.choice(last_names)
            pos = random.choice(positions)
            base = {"QB": (65, 85), "RB": (60, 82), "WR": (60, 84), "TE": (55, 80), "OL": (60, 83), "DL": (60, 84), "LB": (60, 83), "CB": (60, 84), "S": (60, 82), "K": (60, 78), "P": (60, 78)}
            lo, hi = base.get(pos, (60, 80))
            overall = random.randint(lo, hi)
            player = Player.objects.create(
                league=league,
                first_name=first,
                last_name=last,
                position=pos,
                age=22,
                overall_rating=overall,
                potential_rating=min(95, overall + random.randint(5, 20)),
                injury_status="healthy",
                is_rookie_pool=True,
            )
            created.append(player.id)
        return Response({"created": created}, status=status.HTTP_201_CREATED)


class RookiePoolListView(generics.ListAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return Player.objects.filter(league=league, is_rookie_pool=True, team__isnull=True).order_by("-overall_rating")


class DraftCreateView(generics.CreateAPIView):
    serializer_class = DraftSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        season = Season.objects.filter(league=league).order_by("-year").first()
        draft = Draft.objects.create(league=league, season=season, draft_type="rookie")
        # Simple order: by team id
        teams = list(league.teams.order_by("id"))
        overall = 1
        for rnd in range(1, draft.rounds + 1):
            for team in teams:
                DraftPick.objects.create(
                    draft=draft,
                    round_number=rnd,
                    overall_number=overall,
                    team=team,
                    original_team=team,
                )
                overall += 1

        log_action(
            user=request.user,
            action="draft.create",
            entity_type="draft",
            entity_id=draft.id,
            details={"league_id": league.id, "rounds": draft.rounds},
            request=request,
        )
        serializer = self.get_serializer(draft)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DraftDetailView(generics.RetrieveAPIView):
    serializer_class = DraftSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Draft.objects.all()


class DraftPickSelectView(generics.UpdateAPIView):
    serializer_class = DraftPickSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DraftPick.objects.select_related("draft", "player", "team")

    def update(self, request, *args, **kwargs):
        pick = self.get_object()
        draft = pick.draft
        if pick.is_selected:
            return Response({"detail": "Pick already made."}, status=status.HTTP_400_BAD_REQUEST)

        player_id = request.data.get("player_id")
        player = generics.get_object_or_404(Player, pk=player_id)
        # ensure league matches
        if player.league_id and player.league_id != draft.league_id:
            return Response({"detail": "Player not in this league pool."}, status=status.HTTP_400_BAD_REQUEST)
        pick.player = player
        pick.is_selected = True
        pick.selected_at = timezone.now()
        pick.save(update_fields=["player", "is_selected", "selected_at"])
        # assign to team and clear rookie flag
        player.team = pick.team
        player.league = draft.league
        player.is_rookie_pool = False
        player.save(update_fields=["team", "league", "is_rookie_pool"])

        log_action(
            user=request.user,
            action="draft.pick",
            entity_type="draft_pick",
            entity_id=pick.id,
            details={"draft_id": draft.id, "player_id": player.id, "team_id": pick.team_id},
            request=request,
        )
        return Response(self.get_serializer(pick).data)


class StandingsView(generics.GenericAPIView):
    serializer_class = StandingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, league_id, year):
        season = generics.get_object_or_404(Season, league_id=league_id, year=year)
        standings = compute_standings(season)
        serializer = self.get_serializer(standings, many=True)
        return Response(serializer.data)


class GameCompleteView(generics.UpdateAPIView):
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Game.objects.select_related("week")

    def update(self, request, *args, **kwargs):
        game = self.get_object()
        home_score = request.data.get("home_score")
        away_score = request.data.get("away_score")
        if home_score is None or away_score is None:
            return Response({"detail": "Scores required."}, status=status.HTTP_400_BAD_REQUEST)
        game.home_score = int(home_score)
        game.away_score = int(away_score)
        if game.home_score > game.away_score:
            game.winner = game.home_team
            game.loser = game.away_team
        elif game.away_score > game.home_score:
            game.winner = game.away_team
            game.loser = game.home_team
        else:
            game.winner = None
            game.loser = None
        game.status = "completed"
        game.save(update_fields=["home_score", "away_score", "winner", "loser", "status"])

        log_action(
            user=request.user,
            action="game.complete",
            entity_type="game",
            entity_id=game.id,
            details={"week_id": game.week_id, "home": game.home_score, "away": game.away_score},
            request=request,
        )
        return Response(self.get_serializer(game).data)


class PlayoffSeedingView(generics.GenericAPIView):
    serializer_class = PlayoffSeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, league_id, year):
        season = generics.get_object_or_404(Season, league_id=league_id, year=year)
        seeds_raw = generate_playoff_seeds(season)
        seeds = []
        for idx, team_record in enumerate(seeds_raw, start=1):
            team_record["seed"] = idx
            seeds.append(team_record)
        serializer = self.get_serializer(seeds, many=True)
        return Response(serializer.data)


class PlayoffBracketView(generics.GenericAPIView):
    serializer_class = PlayoffMatchupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, league_id, year):
        season = generics.get_object_or_404(Season, league_id=league_id, year=year)
        seeds_raw = generate_playoff_seeds(season, seeds=8)
        # add seed numbers if missing
        for idx, seed in enumerate(seeds_raw, start=1):
            seed.setdefault("seed", idx)
        bracket_pairs = generate_bracket(season, seeds=8)
        data = []
        for higher, lower in bracket_pairs:
            data.append({"higher_seed": higher, "lower_seed": lower})
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


class FreeAgentListView(generics.ListAPIView):
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return Player.objects.filter(league=league, team__isnull=True, is_rookie_pool=False).order_by("-overall_rating")


class FreeAgencyBidView(generics.CreateAPIView):
    serializer_class = FreeAgencyBidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        player_id = request.data.get("player")
        team_id = request.data.get("team")
        amount = request.data.get("amount", 0)
        player = generics.get_object_or_404(Player, pk=player_id, league=league, team__isnull=True, is_rookie_pool=False)
        team = generics.get_object_or_404(Team, pk=team_id, league=league)
        user = request.user
        if not (
            getattr(user, "is_commissioner", False)
            or user.is_staff
            or user.is_superuser
            or team.owner_id == user.id
        ):
            return Response({"detail": "Not authorized to bid for this team."}, status=status.HTTP_403_FORBIDDEN)

        # simple cap/roster checks
        roster_count = team.players.count()
        if roster_count >= league.roster_size_limit:
            return Response({"detail": "Roster limit reached."}, status=status.HTTP_400_BAD_REQUEST)
        current_cap = sum(c.cap_hit for c in team.contracts.all())
        if current_cap + float(amount) > float(league.salary_cap):
            return Response({"detail": "Cap exceeded with this bid."}, status=status.HTTP_400_BAD_REQUEST)

        bid = FreeAgencyBid.objects.create(
            league=league,
            player=player,
            team=team,
            amount=amount,
            mode=league.free_agency_mode,
            status="pending",
            round_number=1,
        )
        log_action(
            user=user,
            action="fa.bid",
            entity_type="fa_bid",
            entity_id=bid.id,
            details={"league_id": league.id, "player_id": player.id, "team_id": team.id, "amount": amount},
            request=request,
        )
        serializer = self.get_serializer(bid)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FreeAgencyResolveView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, league_id):
        league = generics.get_object_or_404(League, pk=league_id)
        pending = FreeAgencyBid.objects.filter(league=league, status="pending").select_related("player", "team")
        awarded = []
        for player_id in pending.values_list("player_id", flat=True).distinct():
            bids = pending.filter(player_id=player_id).order_by("-amount", "created_at")
            if not bids:
                continue
            bid = bids.first()
            team = bid.team
            # cap/roster re-check
            roster_count = team.players.count()
            if roster_count >= league.roster_size_limit:
                continue
            current_cap = sum(c.cap_hit for c in team.contracts.all())
            if current_cap + float(bid.amount) > float(league.salary_cap):
                continue
            # award
            bid.status = "awarded"
            bid.awarded_at = timezone.now()
            bid.save(update_fields=["status", "awarded_at"])
            player = bid.player
            player.team = team
            player.save(update_fields=["team"])
            Contract.objects.create(
                player=player,
                team=team,
                salary=bid.amount,
                bonus=0,
                years=1,
                start_year=timezone.now().year,
            )
            awarded.append(bid.id)
            log_action(
                user=request.user,
                action="fa.award",
                entity_type="fa_bid",
                entity_id=bid.id,
                details={"league_id": league.id, "player_id": player.id, "team_id": team.id, "amount": bid.amount},
                request=request,
            )
        return Response({"awarded": awarded}, status=status.HTTP_200_OK)


class InjuryListCreateView(generics.ListCreateAPIView):
    serializer_class = InjurySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return Injury.objects.filter(league=league).select_related("player")

    def create(self, request, *args, **kwargs):
        league_id = self.kwargs.get("league_id")
        league = generics.get_object_or_404(League, pk=league_id)
        player_id = request.data.get("player")
        player = generics.get_object_or_404(Player, pk=player_id, league=league)
        severity = request.data.get("severity", "minor")
        duration = int(request.data.get("duration_weeks", 1))
        injury = Injury.objects.create(player=player, league=league, severity=severity, duration_weeks=duration)
        player.injury_status = severity
        player.save(update_fields=["injury_status"])
        serializer = self.get_serializer(injury)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InjuryResolveView(generics.UpdateAPIView):
    serializer_class = InjurySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Injury.objects.all()

    def update(self, request, *args, **kwargs):
        injury = self.get_object()
        injury.status = "resolved"
        injury.resolved_at = timezone.now()
        injury.save(update_fields=["status", "resolved_at"])
        # reset player status
        injury.player.injury_status = "healthy"
        injury.player.save(update_fields=["injury_status"])
        serializer = self.get_serializer(injury)
        return Response(serializer.data)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()

    def update(self, request, *args, **kwargs):
        notif = self.get_object()
        if notif.user_id != request.user.id:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        serializer = self.get_serializer(notif)
        return Response(serializer.data)


class GameCompleteView(generics.UpdateAPIView):
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Game.objects.select_related("week")

    def update(self, request, *args, **kwargs):
        game = self.get_object()
        home_score = request.data.get("home_score")
        away_score = request.data.get("away_score")
        if home_score is None or away_score is None:
            return Response({"detail": "Scores required."}, status=status.HTTP_400_BAD_REQUEST)
        game.home_score = int(home_score)
        game.away_score = int(away_score)
        if game.home_score > game.away_score:
            game.winner = game.home_team
            game.loser = game.away_team
        elif game.away_score > game.home_score:
            game.winner = game.away_team
            game.loser = game.home_team
        else:
            game.winner = None
            game.loser = None
        game.status = "completed"
        game.save(update_fields=["home_score", "away_score", "winner", "loser", "status"])

        log_action(
            user=request.user,
            action="game.complete",
            entity_type="game",
            entity_id=game.id,
            details={"week_id": game.week_id, "home": game.home_score, "away": game.away_score},
            request=request,
        )
        return Response(self.get_serializer(game).data)


class ContractUpdateView(generics.UpdateAPIView):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Player.objects.all()

    def get_object(self):
        league_id = self.kwargs.get("league_id")
        player_id = self.kwargs.get("player_id")
        league = generics.get_object_or_404(League, pk=league_id)
        return generics.get_object_or_404(Player.objects.select_related("team"), pk=player_id, team__league=league)

    def update(self, request, *args, **kwargs):
        player = self.get_object()
        team = player.team
        if team is None:
            return Response({"detail": "Player is not on a team."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(
            instance=player.contract if hasattr(player, "contract") else None,
            data=request.data,
            context={"team": team},
        )
        serializer.is_valid(raise_exception=True)
        contract = serializer.save(player=player, team=team)
        log_action(
            user=request.user,
            action="contract.update",
            entity_type="contract",
            entity_id=contract.id,
            details={"league_id": team.league_id, "team_id": team.id, "player_id": player.id},
            request=request,
        )
        return Response(self.get_serializer(contract).data)
