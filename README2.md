# Task Sharding

[![codecov](https://codecov.io/gh/Alexander-Scott/task-sharding/branch/main/graph/badge.svg?token=FJFLCZFUKA)](https://codecov.io/gh/Alexander-Scott/task-sharding)
[![CI](https://github.com/Alexander-Scott/task-sharding/actions/workflows/ci.yml/badge.svg)](https://github.com/Alexander-Scott/task-director/actions/workflows/ci.yml)

## Overview

The idea behind Task Sharding is to allow one large task to be split up into multiple smaller tasks which are then distributed across available clients. It was originally designed with Bazel in mind, with the compilation of most complex targets being distributed amongst clients and the output shared across clients via a remote cache. It is most effective with complex targets that are very low down in the build graph and have an extreme number of dependencies.

### The schema

A schema is a list of steps that the client knows how to interpret. They can be anything from simple integers to bazel build targets. The server does not have knowledge about the content within the steps, rather it knows the total number of steps and the ID of the schema which owns the steps. 

### The server

The server is what facilitates the communication between clients and is what assigns schema steps to individual clients.

### The client

A client connects to the server and supplies client information as well as a schema ID.

## Getting started

### Starting the sever

Fortunately a docker-compose file is provided to allow for a one-command setup.

```bash
docker-compose -f server/docker-compose.yaml up -d
```

### Creating a schema

As mentioned above, a schema file is a YAML file that contains an ID (name) and a list of tasks.

```yaml
name: bazel
steps:
  - task: //:test_my_script_1
  - task: //:test_my_script_2
  - task: //:test_my_script_3

```