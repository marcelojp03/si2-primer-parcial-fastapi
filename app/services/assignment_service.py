class AssignmentService:
    """Intelligent workshop assignment engine.

    TODO: Implement logic considering:
        - incident location
        - incident type
        - workshop availability / schedules
        - workshop specialties
        - distance
        - case priority
    """

    async def find_candidates(self, incident_id: int) -> list[dict]:
        raise NotImplementedError

    async def assign_best(self, incident_id: int) -> dict:
        raise NotImplementedError
