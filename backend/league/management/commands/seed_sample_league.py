from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from league.models import Conference, Division, League, Team

User = get_user_model()


class Command(BaseCommand):
    help = "Create a sample league with default structure and a few teams"

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(email="commish@example.com", defaults={"is_commissioner": True})
        if not user.has_usable_password():
            user.set_password("password123")
            user.save()

        league, created = League.objects.get_or_create(
            name="Sample League",
            created_by=user,
            defaults={
                "conference_count": 2,
                "division_count_per_conference": 2,
                "teams_per_division": 4,
                "free_agency_mode": "auction",
                "allow_cap_growth": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created league '{league.name}'"))
        else:
            self.stdout.write("League already exists; ensuring structure...")

        # Ensure scaffold exists
        conferences = list(Conference.objects.filter(league=league))
        if not conferences:
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
            conferences = list(Conference.objects.filter(league=league))

        # Create a few teams in first division of each conference
        for conf in conferences:
            divisions = list(Division.objects.filter(conference=conf).order_by("order"))
            if not divisions:
                continue
            division = divisions[0]
            base_abbr = conf.name.split()[-1][0].upper()
            for idx in range(1, 3):
                abbr = f"{base_abbr}{idx}"
                team, created = Team.objects.get_or_create(
                    league=league,
                    conference=conf,
                    division=division,
                    abbreviation=abbr,
                    defaults={
                        "name": f"Team {abbr}",
                        "city": f"City {abbr}",
                        "nickname": f"Nick{abbr}",
                        "primary_color": "#123456",
                        "secondary_color": "#abcdef",
                    },
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created team {team}"))

        self.stdout.write(self.style.SUCCESS("Seed complete. User: commish@example.com / password123"))
