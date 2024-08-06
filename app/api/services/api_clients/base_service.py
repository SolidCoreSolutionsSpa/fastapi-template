from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import httpx
from pydantic import BaseModel

from app.core.logger import logger

RequestType = TypeVar("RequestType", bound=BaseModel)
ResponseType = TypeVar("ResponseType", bound=BaseModel)


class BaseService(ABC, Generic[RequestType, ResponseType]):
    """
    Clase abstracta base para servicios que realizan solicitudes HTTP.
    Define la estructura para hacer solicitudes y procesar respuestas.
    """

    @abstractmethod
    def get_endpoint(self) -> str:
        """
        Método abstracto que debe devolver la URL del endpoint del servicio.
        """
        pass

    @abstractmethod
    def parse_response(self, response: dict[str, any]) -> ResponseType:
        """
        Método abstracto que debe analizar la respuesta en el tipo de respuesta deseado.
        """
        pass

    async def make_request(
        self, request_data: RequestType, access_token: str, base_url: str
    ) -> ResponseType | None:
        """
        Realiza una solicitud HTTP GET asincrónica con los datos de la solicitud y devuelve la respuesta parseada.

        Args:
            request_data: Datos de la solicitud.
            access_token: Token de acceso para la autenticación.
            base_url: URL base del servicio.

        Returns:
            Una instancia de ResponseType si la solicitud y el parseo son exitosos, None en caso contrario.

        Raises:
            HTTPStatusError: Si ocurre un error HTTP durante la solicitud.
            Exception: Para cualquier otro tipo de error.
        """
        endpoint = self.get_endpoint()
        url = f"{base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = request_data.model_dump(by_alias=True)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=15,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    f"Error response {exc.response.status_code} while making request to {url}. Response content: {exc.response.content.decode('utf-8')}"
                )
                raise exc
            except Exception as exc:
                logger.error(
                    f"An error occurred while making request to {url}: {str(exc)}"
                )
                raise exc

            logger.info(
                f"{self.__class__.__name__} with params {params} request successful"
            )
            response_data = response.json()
            try:
                return self.parse_response(response_data)
            except Exception as exc:
                logger.error(
                    f"An error occurred while parsing response from {url} with params {params}"
                )
                raise exc
