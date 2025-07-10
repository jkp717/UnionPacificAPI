UnionPacificAPI is an unofficial Python client library for the Union Pacific Railroad REST API.

### Usage Example...
```
from union_pacific_api import UPClient


if __name__ == "__main__":

    # Initialize UPClient either with .env file or by passing credentials
    # api = UPClient(userid='xxxxxxx', password='password')
    api = UPClient()  # using .env file

    origin_loc = api.get_locations(splc='883012')
    destination_loc = api.get_locations(splc='261200')
    
    # Get the location ID from the get_locations call
    origin_id = origin_loc[0].id
    destination_id = destination_loc[0].id
    
    # Get the route options from O/D pair
    routes = api.get_routes(origin_loc[0].id, destination_loc[0].id)
    
    # Print unique routes
    unique_routes = set([r for r in routes])
    for r in unique_routes:
        print(r.route_str, r.destination_rr)
```
