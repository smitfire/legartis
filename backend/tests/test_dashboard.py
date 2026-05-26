from typing import Any

from httpx import AsyncClient


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


async def test_lists_uploaded_documents_in_creation_order(client: AsyncClient) -> None:
    first = await _upload(client, "first.txt", "Alpha sentence.")
    second = await _upload(client, "second.txt", "Bravo sentence.")

    response = await client.get("/documents")

    assert response.status_code == 200
    titles = [d["title"] for d in response.json()]
    assert titles == ["first.txt", "second.txt"]
    assert {first["id"], second["id"]} == {d["id"] for d in response.json()}


async def test_filters_by_q_against_title_and_content_case_insensitively(
    client: AsyncClient,
) -> None:
    await _upload(client, "nda.txt", "Confidential information stays confidential.")
    await _upload(client, "service-agreement.md", "The provider limits liability.")

    response = await client.get("/documents", params={"q": "LIABILITY"})

    assert [d["title"] for d in response.json()] == ["service-agreement.md"]


async def test_filters_by_single_clause_type(client: AsyncClient) -> None:
    nda = await _upload(client, "nda.txt", "Each party shall keep the data confidential.")
    msa = await _upload(client, "msa.txt", "Provider limits liability to fees paid.")
    await _label(client, nda["sentences"][0]["id"], "confidentiality")
    await _label(client, msa["sentences"][0]["id"], "limitation_of_liability")

    response = await client.get("/documents", params={"type": "confidentiality"})

    assert [d["title"] for d in response.json()] == ["nda.txt"]


async def test_multi_select_types_are_or_ed_together(client: AsyncClient) -> None:
    nda = await _upload(client, "nda.txt", "Each party shall keep the data confidential.")
    msa = await _upload(client, "msa.txt", "Provider limits liability to fees paid.")
    extra = await _upload(client, "untouched.txt", "Boilerplate sentence.")
    await _label(client, nda["sentences"][0]["id"], "confidentiality")
    await _label(client, msa["sentences"][0]["id"], "limitation_of_liability")

    response = await client.get(
        "/documents",
        params=[("type", "confidentiality"), ("type", "limitation_of_liability")],
    )

    titles = {d["title"] for d in response.json()}
    assert titles == {"nda.txt", "msa.txt"}
    assert "untouched.txt" not in titles
    assert extra["id"] not in {d["id"] for d in response.json()}


async def test_group_by_type_returns_groups_keyed_by_clause_type(client: AsyncClient) -> None:
    nda = await _upload(client, "nda.txt", "Each party shall keep the data confidential.")
    msa = await _upload(client, "msa.txt", "Provider limits liability to fees paid.")
    both = await _upload(client, "combo.txt", "Confidential. Limits liability.")
    await _label(client, nda["sentences"][0]["id"], "confidentiality")
    await _label(client, msa["sentences"][0]["id"], "limitation_of_liability")
    await _label(client, both["sentences"][0]["id"], "confidentiality")
    await _label(client, both["sentences"][1]["id"], "limitation_of_liability")

    response = await client.get("/documents", params={"group_by": "type"})

    payload = response.json()
    assert response.status_code == 200
    groups = {g["clause_type"]: [d["title"] for d in g["documents"]] for g in payload["groups"]}
    assert set(groups["confidentiality"]) == {"nda.txt", "combo.txt"}
    assert set(groups["limitation_of_liability"]) == {"msa.txt", "combo.txt"}


async def test_dashboard_summary_includes_label_count_per_document(client: AsyncClient) -> None:
    doc = await _upload(client, "a.txt", "First. Second.")
    await _label(client, doc["sentences"][0]["id"], "confidentiality")
    await _label(client, doc["sentences"][1]["id"], "non_compete")

    response = await client.get("/documents")

    [summary] = response.json()
    assert summary["sentence_count"] == 2
    assert summary["label_count"] == 2
    assert set(summary["clause_types"]) == {"confidentiality", "non_compete"}
