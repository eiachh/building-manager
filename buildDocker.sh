#!/bin/bash

eval $(minikube docker-env)
docker build -t eiachh/build-manager ./