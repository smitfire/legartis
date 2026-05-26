from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClauseType


async def _upload(client: AsyncClient, name: str, body: str) -> dict[str, Any]:
    response = await client.post(
        "/documents",
        files={"file": (name, body.encode("utf-8"), "text/plain")},
    )
    payload: dict[str, Any] = response.json()
    return payload


async def _label(client: AsyncClient, sentence_id: int, clause_type: str) -> None:
    response = await client.post(
        f"/sentences/{sentence_id}/labels",
        json={"clause_type": clause_type},
    )
    assert response.status_code == 201


async def test_lists_seven_seeded_clause_types(client: AsyncClient) -> None:
    response = await client.get("/clause-types")

    assert response.status_code == 200
    payload = response.json()
    assert {item["label"] for item in payload} == {
        "Limitation of Liability",
        "Termination for Convenience",
        "Non-Compete",
        "Confidentiality",
        "Governing Law",
        "Indemnification",
        "Force Majeure",
    }


async def test_lists_clause_types_added_to_the_database(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    db_session.add(ClauseType(value="force_majeure_lite", label="Force Majeure Lite"))
    await db_session.commit()

    response = await client.get("/clause-types")

    by_label = {item["label"]: item["value"] for item in response.json()}
    assert by_label["Force Majeure Lite"] == "force_majeure_lite"


async def test_each_clause_type_has_stable_machine_value(client: AsyncClient) -> None:
    response = await client.get("/clause-types")

    by_label = {item["label"]: item["value"] for item in response.json()}
    assert by_label["Limitation of Liability"] == "limitation_of_liability"
    assert by_label["Non-Compete"] == "non_compete"


async def test_clause_type_counts_returns_zero_for_every_type_when_no_labels(
    client: AsyncClient,
) -> None:
    response = await client.get("/clause-type-counts")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 7
    assert all(entry["count"] == 0 for entry in payload)


async def test_clause_type_counts_counts_distinct_documents_not_labels(
    client: AsyncClient,
) -> None:
    nda = await _upload(client, "nda.txt", "Confidential. More confidential text.")
    msa = await _upload(client, "msa.txt", "Liability is capped. Also confidential here.")
    # Same document labelled twice with the same type → still one document.
    await _label(client, nda["sentences"][0]["id"], "confidentiality")
    await _label(client, nda["sentences"][1]["id"], "confidentiality")
    await _label(client, msa["sentences"][0]["id"], "limitation_of_liability")
    await _label(client, msa["sentences"][1]["id"], "confidentiality")

    response = await client.get("/clause-type-counts")

    counts = {entry["value"]: entry["count"] for entry in response.json()}
    assert counts["confidentiality"] == 2  # nda and msa
    assert counts["limitation_of_liability"] == 1  # msa only
    assert counts["non_compete"] == 0


async def test_create_clause_type_returns_201_with_slugified_value(client: AsyncClient) -> None:
    response = await client.post("/clause-types", json={"label": "Service Level Agreement"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["label"] == "Service Level Agreement"
    assert payload["value"] == "service_level_agreement"
    assert isinstance(payload["id"], int)


async def test_create_clause_type_with_colliding_label_suffixes_value(
    client: AsyncClient,
) -> None:
    first = await client.post("/clause-types", json={"label": "Force Majeure"})
    second = await client.post("/clause-types", json={"label": "Force Majeure"})

    # First request collides with the existing seed value; both new posts must succeed
    # silently with auto-suffixed machine values rather than erroring out.
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["value"] == "force_majeure_2"
    assert second.json()["value"] == "force_majeure_3"


async def test_patch_clause_type_updates_label_only(client: AsyncClient) -> None:
    created = (await client.post("/clause-types", json={"label": "Termination"})).json()

    patched = await client.patch(
        f"/clause-types/{created['id']}",
        json={"label": "Termination for Cause"},
    )

    assert patched.status_code == 200
    body = patched.json()
    assert body["label"] == "Termination for Cause"
    assert body["value"] == created["value"]


async def test_patch_unknown_clause_type_returns_404(client: AsyncClient) -> None:
    response = await client.patch("/clause-types/99999", json={"label": "Whatever"})

    assert response.status_code == 404


async def test_delete_clause_type_cascades_to_labels(client: AsyncClient) -> None:
    doc = await _upload(client, "msa.txt", "Confidential terms apply.")
    sentence_id = doc["sentences"][0]["id"]
    await _label(client, sentence_id, "confidentiality")
    options = (await client.get("/clause-types")).json()
    type_id = next(opt for opt in options if opt["value"] == "confidentiality")["id"]

    response = await client.delete(f"/clause-types/{type_id}")

    assert response.status_code == 204
    after = (await client.get(f"/documents/{doc['id']}")).json()
    assert after["sentences"][0]["labels"] == []


async def test_delete_unknown_clause_type_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/clause-types/99999")

    assert response.status_code == 404


async def test_clause_type_counts_respects_search_query(client: AsyncClient) -> None:
    nda = await _upload(client, "nda.txt", "Confidential information only.")
    msa = await _upload(client, "msa.txt", "Liability is capped at fees paid.")
    await _label(client, nda["sentences"][0]["id"], "confidentiality")
    await _label(client, msa["sentences"][0]["id"], "limitation_of_liability")

    response = await client.get("/clause-type-counts", params={"q": "liability"})

    counts = {entry["value"]: entry["count"] for entry in response.json()}
    assert counts["limitation_of_liability"] == 1  # msa matches "liability"
    assert counts["confidentiality"] == 0  # nda does not match "liability"
