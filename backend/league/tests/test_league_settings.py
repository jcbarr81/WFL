import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from users.models import User

pytestmark = pytest.mark.django_db


def auth_client(email, is_commish=False):
    user = User.objects.create_user(email=email, password="password123", is_commissioner=is_commish)
    client = APIClient()
    client.post(reverse("users:login"), {"email": email, "password": "password123"}, format="json")
    return client, user


def create_league(client):
    resp = client.post(reverse("league:league-list-create"), {"name": "League"}, format="json")
    assert resp.status_code == 201
    return resp.json()["id"]


def test_league_update_requires_commish_or_creator():
    client, _ = auth_client("owner@example.com", is_commish=False)
    league_id = create_league(client)

    other_client, _ = auth_client("other@example.com", is_commish=False)
    url = reverse("league:league-update", args=[league_id])
    forbidden = other_client.patch(url, {"free_agency_mode": "rounds"}, format="json")
    assert forbidden.status_code == 403

    commish_client, _ = auth_client("commish@example.com", is_commish=True)
    ok_resp = commish_client.patch(url, {"free_agency_mode": "rounds", "allow_cap_growth": True}, format="json")
    assert ok_resp.status_code == 200
    body = ok_resp.json()
    assert body["free_agency_mode"] == "rounds"
    assert body["allow_cap_growth"] is True


def test_commish_can_rename_conference_and_division():
    client, _ = auth_client("commish@example.com", is_commish=True)
    league_id = create_league(client)

    structure = client.get(reverse("league:league-structure", args=[league_id])).json()
    conf_id = structure["conferences"][0]["id"]
    div_id = structure["conferences"][0]["divisions"][0]["id"]

    conf_url = reverse("league:conference-rename", args=[league_id, conf_id])
    div_url = reverse("league:division-rename", args=[league_id, div_id])

    resp_conf = client.patch(conf_url, {"name": "Renamed Conf"}, format="json")
    assert resp_conf.status_code == 200
    assert resp_conf.json()["name"] == "Renamed Conf"

    resp_div = client.patch(div_url, {"name": "Renamed Div"}, format="json")
    assert resp_div.status_code == 200
    assert resp_div.json()["name"] == "Renamed Div"
