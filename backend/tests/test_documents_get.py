from httpx import AsyncClient


async def test_get_document_returns_404_for_unknown_id(client: AsyncClient) -> None:
    response = await client.get("/documents/999")
    assert response.status_code == 404


async def test_get_document_returns_full_document_with_sentences(client: AsyncClient) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("nda.txt", b"First sentence. Second sentence.", "text/plain")},
    )
    doc_id = upload.json()["id"]

    response = await client.get(f"/documents/{doc_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == doc_id
    assert body["title"] == "nda.txt"
    assert [s["text"] for s in body["sentences"]] == ["First sentence.", "Second sentence."]
    assert all(s["labels"] == [] for s in body["sentences"])
