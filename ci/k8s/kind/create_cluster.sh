#!/usr/bin/env bash
set -euo pipefail

kind create cluster --name dev-1 --config ci/k8s/kind/dev-1.yaml
docker network connect data-platform-net dev-1-control-plane
docker network connect secrets-net dev-1-control-plane