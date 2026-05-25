from typing import Any

from httpx import AsyncClient


async def _upload(client: AsyncClient, name: str, body: str) -> dict[str, Any]:
    response = await client.post(
        "/documents",
        files={"file": (name, body.encode("utf-8"), "text/plain")},
    )
    return response.json()


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


async def test_clause_type_counts_respects_search_query(client: AsyncClient) -> None:
    nda = await _upload(client, "nda.txt", "Confidential information only.")
    msa = await _upload(client, "msa.txt", "Liability is capped at fees paid.")
    await _label(client, nda["sentences"][0]["id"], "confidentiality")
    await _label(client, msa["sentences"][0]["id"], "limitation_of_liability")

    response = await client.get("/clause-type-counts", params={"q": "liability"})

    counts = {entry["value"]: entry["count"] for entry in response.json()}
    assert counts["limitation_of_liability"] == 1  # msa matches "liability"
    assert counts["confidentiality"] == 0  # nda does not match "liability"
