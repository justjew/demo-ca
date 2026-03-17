import uuid
from dataclasses import dataclass

from ..entities.client import Client
from ..interfaces.repositories import IClientRepository
from .crud import CrudUseCase


@dataclass
class ClientCreateDTO:
    phone_number: str
    first_name: str | None = None
    last_name: str | None = None


@dataclass
class ClientUpdateDTO:
    phone_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class ClientCrudUseCase(CrudUseCase[Client, ClientCreateDTO, ClientUpdateDTO]):
    entity_name = "Client"

    def __init__(self, client_repo: IClientRepository):
        super().__init__(client_repo)
        self._client_repo = client_repo

    def _build_entity(self, data: ClientCreateDTO) -> Client:
        return Client(
            id=uuid.uuid4(),
            phone_number=data.phone_number,
            first_name=data.first_name,
            last_name=data.last_name,
        )

    def _save(self, entity: Client) -> None:
        self._client_repo.save_client(entity)
