from httpx import AsyncClient


async def test_upload_returns_document_with_one_sentence_for_single_sentence_text(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/documents",
        files={"file": ("contract.txt", b"Hello world.", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "contract.txt"
    assert [s["text"] for s in body["sentences"]] == ["Hello world."]
    assert body["sentences"][0]["position"] == 0
