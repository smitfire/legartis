from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def _upload(client: AsyncClient, body: bytes = b"First. Second. Third.") -> dict[str, Any]:
    response = await client.post(
        "/documents",
        files={"file": ("contract.txt", body, "text/plain")},
    )
    return response.json()


async def test_creates_label_on_sentence_and_returns_201(client: AsyncClient) -> None:
    doc = await _upload(client)
    sentence_id = doc["sentences"][0]["id"]

    response = await client.post(
        f"/sentences/{sentence_id}/labels",
        json={"clause_type": "limitation_of_liability"},
    )

    assert response.status_code == 201
    label = response.json()
    assert label["sentence_id"] == sentence_id
    assert label["clause_type"] == "limitation_of_liability"
    assert label["source"] == "MANUAL"
    assert label["confidence"] is None


async def test_label_appears_in_subsequent_get_document(client: AsyncClient) -> None:
    doc = await _upload(client)
    sentence_id = doc["sentences"][1]["id"]
    await client.post(
        f"/sentences/{sentence_id}/labels",
        json={"clause_type": "confidentiality"},
    )

    refreshed = (await client.get(f"/documents/{doc['id']}")).json()

    second_sentence = refreshed["sentences"][1]
    assert [lb["clause_type"] for lb in second_sentence["labels"]] == ["confidentiality"]


async def test_duplicate_label_on_same_sentence_returns_409(client: AsyncClient) -> None:
    doc = await _upload(client)
    sentence_id = doc["sentences"][0]["id"]
    body = {"clause_type": "non_compete"}
    first = await client.post(f"/sentences/{sentence_id}/labels", json=body)
    assert first.status_code == 201

    second = await client.post(f"/sentences/{sentence_id}/labels", json=body)

    assert second.status_code == 409


async def test_label_on_unknown_sentence_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        "/sentences/9999/labels",
        json={"clause_type": "non_compete"},
    )
    assert response.status_code == 404


async def test_label_with_invalid_clause_type_returns_422(client: AsyncClient) -> None:
    doc = await _upload(client)
    sentence_id = doc["sentences"][0]["id"]

    response = await client.post(
        f"/sentences/{sentence_id}/labels",
        json={"clause_type": "not-a-real-type"},
    )

    assert response.status_code == 422


async def test_delete_label_returns_204_and_removes_it(client: AsyncClient) -> None:
    doc = await _upload(client)
    sentence_id = doc["sentences"][0]["id"]
    create = await client.post(
        f"/sentences/{sentence_id}/labels",
        json={"clause_type": "force_majeure"},
    )
    label_id = create.json()["id"]

    delete = await client.delete(f"/labels/{label_id}")

    assert delete.status_code == 204
    refreshed = (await client.get(f"/documents/{doc['id']}")).json()
    assert refreshed["sentences"][0]["labels"] == []


async def test_delete_unknown_label_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/labels/12345")
    assert response.status_code == 404


async def test_deleting_document_cascades_to_labels(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from sqlalchemy import func, select

    from app.models import Document, Label

    doc = await _upload(client)
    sentence_id = doc["sentences"][0]["id"]
    await client.post(
        f"/sentences/{sentence_id}/labels",
        json={"clause_type": "indemnification"},
    )

    document = await db_session.get(Document, doc["id"])
    assert document is not None
    await db_session.delete(document)
    await db_session.commit()

    remaining = await db_session.scalar(select(func.count()).select_from(Label))
    assert remaining == 0
