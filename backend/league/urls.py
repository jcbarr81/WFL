from django.urls import path

from .views import (
    LeagueDetailView,
    LeagueListCreateView,
    LeagueStructureView,
    TeamRosterReleaseView,
    TeamRosterCreateView,
    TeamRosterView,
    TeamCreateView,
    TeamListView,
)

app_name = "league"

urlpatterns = [
    path("leagues/", LeagueListCreateView.as_view(), name="league-list-create"),
    path("leagues/<int:pk>/", LeagueDetailView.as_view(), name="league-detail"),
    path("leagues/<int:pk>/structure/", LeagueStructureView.as_view(), name="league-structure"),
    path("leagues/<int:league_id>/teams/", TeamListView.as_view(), name="team-list"),
    path("leagues/<int:league_id>/teams/create/", TeamCreateView.as_view(), name="team-create"),
    path("leagues/<int:league_id>/teams/<int:team_id>/roster/", TeamRosterView.as_view(), name="team-roster"),
    path("leagues/<int:league_id>/teams/<int:team_id>/roster/add/", TeamRosterCreateView.as_view(), name="team-roster-add"),
    path("leagues/<int:league_id>/teams/<int:team_id>/roster/<int:player_id>/release/", TeamRosterReleaseView.as_view(), name="team-roster-release"),
]
