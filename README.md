UnionPacificAPI is an unofficial Python library for the Union Pacific Railroad REST API.

### Usage Example...
```
from UnionPacificAPI import UnionPacificAPI


if __name__ == "__main__":
    # api = UnionPacificAPI(userid='xxxxxxx', password='password')
    api = UnionPacificAPI()  # using .env file
    # locations = api.get_location_by_splc(splc="424250000")
    shp = api.get_shipment_by_id('c6a77911-9e01-4e8b-857a-36a64a20e221')
```
