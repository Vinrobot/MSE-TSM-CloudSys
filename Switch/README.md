# SwitchEngine

- https://engines.admin.switch.ch
- https://engines.switch.ch/horizon/quickstart/

## Setup

1) Create file `~/.config/openstack/clouds.yaml` with:
```yaml
clouds:
  switchengine:
    region_name: ZH
    auth:
      username: <USERNAME>
      password: <PASSWORD>
      project_name: Master-Cloud12
      auth_url: https://keystone.cloud.switch.ch:5000/v3
      user_domain_name: Default
      project_domain_name: Default
```

2) `pip install -r requirements.txt`
