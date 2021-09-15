import argparse
import json
import requests

# The API endpoints are specified over here
urlCompute = "http://10.1.75.20:8774/v2.1/"
urlIdentity = "http://10.1.75.20:5000/v3/"
urlNetwork = "http://10.1.75.20:9696/v2.0/"


# Remove the instances, network and router to start the project fresh
def clearProject(authToken, projectID):
    #remove instances
    print("[*] Deleting Instances")

    response = requests.get(urlCompute + projectID + "/servers", headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })
    servers = json.loads(response.text)["servers"]
    for server in servers:
        serverID = server["id"]
        response = requests.delete(urlCompute + projectID + "/servers/" + serverID, headers={
            "content-type": "application/json",
            "x-auth-token": authToken
        })

    print("[+] Instances Removed")

    #remove routers
    print("[*] Deleting Routers")

    response = requests.get(urlNetwork + "subnets", headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })
    subnets = json.loads(response.text)["subnets"]
   
    response = requests.get(urlNetwork + "routers", headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })

    routers = json.loads(response.text)["routers"]

    for router in routers:
        routerID = router["id"]

        for subnet in subnets:
            data = {    "subnet_id" : subnet["id"]  }
            response = requests.put(urlNetwork + "routers/" + routerID + "/remove_router_interface", json.dumps(data), headers={
                "content-type": "application/json",
                "x-auth-token": authToken
            })
            

        response = requests.delete(urlNetwork + "routers/" + routerID, headers={
            "content-type": "application/json",
            "x-auth-token": authToken
        })

    print("[+] Routers Removed")


    #remove networks
    print("[*] Deleting Networks")

    response = requests.get(urlNetwork + "networks", headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })
    networks = json.loads(response.text)["networks"]
    for network in networks:
        if network["name"] == "external_network":   continue
        networkID = network["id"]
        response = requests.delete(urlNetwork + "networks/" + networkID, headers={
            "content-type": "application/json",
            "x-auth-token": authToken
        })

    print("[+] Networks Removed")

    exit(0)


# Create the ubuntu instances
def createInstances(authToken, networkID, projectID):
    print("[*] Creating Instances")

    data = {
        "server": {
            "name": "InternalTestServer",
            "imageRef": "84e573aa-2501-4e10-b624-7584ccb005a9",
            "flavorRef": "d57fda8e-dffd-4350-a517-64bc2b9d1c0e",
            "OS-DCF:diskConfig": "AUTO",
            "min_count": 2,
            "networks": [
                {
                    "uuid": networkID
                }
            ]
        }
    }

    requests.post(urlCompute + projectID + "/servers", json.dumps(data), headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })

    print("[+] Instances Created")


# Create the network and subnet along with adding the subnet to the internal network
def createNetwork(authToken):
    print("[*] Creating Network")

    data = {
        "networks": [
            {
                "admin_state_up": 'true',
                "name": "InternalTestNetwork"
            }
        ]
    }

    response = requests.post(urlNetwork + "networks", json.dumps(data), headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })

    networkID = json.loads(response.text)['networks'][0]['id']

    print("[+] Network Created")
    print("[*] Creating Subnet")

    subnetID = createSubnet(authToken, networkID)

    print("[+] Subnet Created")
    return networkID, subnetID


# Create the router and add it to the external, internal networks
def createRouter(authToken, subnetID):
    print("[*] Creating Router")

    response = requests.get(urlNetwork + "networks", headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })
    response = json.loads(response.text)

    for network in response["networks"]:
        if network["name"] == "external_network":
            extNetworkID = network["id"]
            break

    data = {
        "router": {
            "name": "InternalTestRouter",
            "external_gateway_info": {
                "network_id": extNetworkID
            },
            "admin_state_up": True
        }
    }

    response = requests.post(urlNetwork + "routers", json.dumps(data), headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })

    routerID = json.loads(response.text)['router']['id']

    print("[+] Router Created")

    print("[*] Connecting Netorks")

    data = {
        "subnet_id": subnetID
    }

    response = requests.put(urlNetwork + "routers/" + routerID + "/add_router_interface", json.dumps(data), headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })

    print("[+] Router Interface Added")


# Create the subnet for the internal netowrk
def createSubnet(authToken, networkID):
    data = {
        "subnet": {
            "name": "InternalTestSubnet",
            "network_id": networkID,
            "ip_version": 4,
            "cidr": "192.168.1.0/24"
        }
    }

    response = requests.post(urlNetwork + "subnets", json.dumps(data), headers={
        "content-type": "application/json",
        "x-auth-token": authToken
    })

    subnetID = json.loads(response.text)['subnet']['id']
    return subnetID


# Get the auth key from the identity API for the project
def getToken(username, password):
    print("[*] Authenticating")

    data = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "name": username,
                        "domain": {
                            "id": "default"
                        },
                        "password": password
                    }
                }
            }
        }
    }

    response = requests.post(urlIdentity + "auth/tokens", json.dumps(data),
                             headers={"content-type": "application/json"})

    userID = json.loads(response.text)['token']['user']['id']
    authToken = response.headers["X-Subject-Token"]

    response = requests.get(urlIdentity + "users/" + userID + "/projects", headers={
        'x-auth-token': authToken
    })
    projectID = json.loads(response.text)["projects"][0]["id"]

    data["auth"]["scope"] = {
        "project": {
            "domain": {
                "name": "Default"
            },
            "id": projectID
        }
    }

    response = requests.post(urlIdentity + "auth/tokens", json.dumps(data),
                             headers={"content-type": "application/json"})
    authToken = response.headers["X-Subject-Token"]

    print("[+] Authentication Completed")
    return authToken, projectID


def main():
    args = parse_arguments()
    username = args.username
    password = args.password

    authToken, projectID = getToken(username, password)

    if args.clearall:
        clearProject(authToken, projectID)

    networkID, subnetID = createNetwork(authToken)

    createRouter(authToken, subnetID)

    createInstances(authToken, networkID, projectID)

    print("[+] Successfully Completed")


# Parse and get the command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="OpenStack Network Automation V1.0",
    )
    parser.add_argument('-u', '--username',
                        help="Username to log in to", required=True)
    parser.add_argument('-p', '--password',
                        help="Password for the account", required=True)
    parser.add_argument('-pid', '--project',
                        help="Project ID")
    parser.add_argument('-c', '--clearall', action="store_true",
                        help="Remove all the instanes and networks", required=False)

    return parser.parse_args()


if __name__ == "__main__":
    main()
