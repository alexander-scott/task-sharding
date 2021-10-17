# Task Director

## Overview

Task Director is essentially a P2P load balancer. It receives tasks from peers and then distributes tasks over all available peers. It uses a centralised system, meaning a server instance needs to be up and running and peers need to have knowledge of the server.

### Background

## Overview

### 1 Existing setup

The Task Director is perfect for peers which each have identical or similar tasks that need to be completed. An example of the perfect scenario is shown below. In the diagram there are three peers who need to perform the same six tasks. In this scenario, a task is a unit of work whose result/output can be shared amongst all peers.

![Overview](docs/images/1_Overview.svg)

How do we get all peers to have the result of all of their tasks? There are two obvious ways: schedule the each peer to run their tasks in parallel, or schedule each peer to run their tasks linearly.

### 1 Linear Execution

![Linear](docs/images/1_Linear_Example.svg)

### 1 Parallel Execution

![Parallel](docs/images/1_Parallel_Example.svg)

### 2 Proposed Setup

![Task Directory](docs/images/2_Task_Director.svg)
