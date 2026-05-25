from httpx import AsyncClient


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
