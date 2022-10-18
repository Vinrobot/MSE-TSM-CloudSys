- What happens if you delete a Frontend or API Pod? How long does it take for the system to react?

Kubernetes create a new pod.
It's fast

- What happens when you delete the Redis Pod?

All the data are lost, Sadge.
We have to configure a volume and redis to store the data in the volume.

- How can you change the number of instances temporarily to 3? Hint: look for scaling in the deployment documentation

kubectl scale deploy/frontend-api --replicas=3

- What autoscaling features are available? Which metrics are used?

You choose the metrics (storage, memory, cpu, gpu, ...)

- How can you update a component? (see update in the deployment documentation)

By modifying the manifests and re-applying it
