# OpenStack-Automation
To automate creation of a simple network in OpenStack.

The network consistes of the follwing devices:
```
1. An internal network with subnet 192.168.1/24
2. A router to connect internal subnet to external gateway
3. 2 Ubuntu instances
```

![Netowork Created](network.jpg?raw=true)

# Usage

Install requirements
> pip3 install -r requirements.txt

Run the Script

1. To clear the project (remove instances, netowrks, routers)

> python3 OpenStackAutomate.py -u <username> -p <password>


2. To create the network

> python3 OpenStackAutomate.py -u username -p password -c


Help menu:
> python3 OpenStackAutomate.py --help


# Working
This script works by calling the OpenStack API to perform the following:
1. Calls the Identity API to generate a token for authorization.
2. Gets the projects from the Identity API and creates another auth token with the scope of the project.
3. Creates an internal network with the name "InternalTestNetwork"
4. Creates a subnet for the newly made network and associates them.
5. Creates a router, connects it to the external network and the newly created internal network.
6. Finally creates 2 ubuntu instances on the internal network.
