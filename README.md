UnionPacificAPI is an unofficial Python client library for the Union Pacific Railroad REST API.

### Usage Example...
```
from union_pacific_api import UPClient


if __name__ == "__main__":
    # api = UPClient(userid='xxxxxxx', password='password')
    api = UPClient()  # using .env file
    # locations = api.get_locations(splc="424250000")
    shp = api.get_shipment_by_id('c6a77911-9e01-4e8b-857a-36a64a20e221')
```
