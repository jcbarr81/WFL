from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import League, Player, Team
from .serializers import (
    LeagueSerializer,
    LeagueStructureSerializer,
    PlayerSerializer,
    TeamSerializer,
)
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


class LeagueStructureView(generics.RetrieveAPIView):
    serializer_class = LeagueStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = League.objects.all()


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
        team = serializer.save(league=league)
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
