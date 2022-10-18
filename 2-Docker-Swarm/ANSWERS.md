# How does Swarm deal with the loss of a replica?
The lost replicas are scheduled on the remaining nodes based on their charge of the nodes

# How can you update the numbers of replicas without re-deploying with the docker-compose file?
```shell
$ docker service scale todo_api=2
```

# Is there a default way to auto-scale with Swarm?
There is no default way to auto-scale, but there are third-party tools.
