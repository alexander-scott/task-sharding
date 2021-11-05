# Task Director

## Overview

Task Director is essentially a P2P load balancer. It receives tasks from peers and then distributes tasks over all available peers. It uses a centralised system, meaning a server instance needs to be up and running and peers need to have knowledge of the server.

### Background

## Overview

### 1 Existing setup

The Task Director is perfect for peers which each have identical or similar tasks that need to be completed. An example of the perfect scenario is shown below. In the diagram there are three peers who need to perform the same six tasks. In this scenario, a task is a unit of work whose result/output can be shared amongst all peers.

![Overview](docs/images/1_Overview.svg)

How do we get all peers to have the result of all of their tasks? There are two obvious ways: schedule the each peer to run their tasks in parallel, or schedule each peer to run their tasks linearly.

#### 1 Linear Execution

![Linear](docs/images/1_Linear_Example.svg)

#### 1 Parallel Execution

![Parallel](docs/images/1_Parallel_Example.svg)

### 2 Proposed Setup

![Task Director](docs/images/2_Task_Director.svg)

The task director aims to distribute and prioritise tasks between available peers.

### Peers

Once a peer is ready to build, it will send the following data to the central authority:

- Peer name/ID
- Base ref (e.g. master)
- Change ref / PR number
- Repository
- Pipeline name
- Pipeline type (independent or dependent)
- Remote Cache ID (e.g. muc9 or muc10)
- Task Schema ID
- Current task

Peers will deregister themselves during a post-run and cleanup-run.

During the main run/build step, a python process will request will ask the central authority what to build, and will build the requested targets.

### The Central Authority

The Central Authority will receive task requests and prioritise them accordingly.

### Example Scenario 1

#### A new peer has entered the gate pipeline

Once the peer is ready, it sends the following message to the Central Authority:

```
curl \
  --request POST \
  --data '{ \
      "peer_id": "42", \
      "base_ref": "master", \
      "change_ref": "123456", \
      "repository": "swh/ddad_ci_config", \
      "pipeline": "gate", \
      "pipeline_type": "dependent", \
      "remote_cache_id": "muc9", \
      "task_schema_id": "adp_fastbuild", \
      "current_task": -1, \
      }' \
  http://localhost:10000/new_peer
```

The specified task schema, `adp_fastbuild`, looks like this:

```json
{
	"1": "//application/adp/common/...",
	"2": "//application/adp/planning/...",
	"3": "//application/adp/perception/...",
	"4": "//application/adp/test/..."
}
```

The Central Authority then responds instructing this peer with ID `42` to build task `1` within the `adp_fastbuild` schema.

If another peer were to join after this peer, it would be instructed to build a different task, e.g. task `2`, as task `1` is already in progress.
