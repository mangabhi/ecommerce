# Docker and Kubernetes README

This guide describes the Docker and Kubernetes files currently in this
repository and walks through building, running, and checking the application.
Commands are written for PowerShell and should be run from the repository root
unless a step says otherwise.

## What is included

- `backend/Dockerfile` builds the FastAPI image.
- `frontend/Dockerfile` builds the Next.js image.
- `compose.yaml` builds and runs both containers together.
- `k8s/namespace.yaml` creates the `ecommerce` Kubernetes namespace.
- `k8s/backend-deployment.yaml` runs one backend replica.

The Kubernetes files do not currently define a frontend Deployment, a Service,
or the backend's environment variables. The Kubernetes section explains how to
supply the required backend configuration and access the backend while testing.

## Prerequisites

- Docker Desktop with Docker Compose enabled.
- PowerShell.
- For the Kubernetes steps: a running Kubernetes cluster and `kubectl`
  configured to use it. To publish the image, a Docker Hub account or another
  accessible image registry is also required.
- Backend and frontend Docker environment files:
  `backend/.env.docker` and `frontend/.env.docker`. Keep these files private;
  they are excluded from the Docker build contexts by the `.dockerignore`
  files. The backend needs `DB_CONNECTION`, `SECRET_KEY`, `ALGORITHM`,
  `EXP_TIME`, and `REFRESH_EXP_TIME`. See [backend/README.md](backend/README.md)
  for the backend environment details.

## 1. Build images individually (optional)

Compose builds the images for you in the next section. Build them individually
if you want to inspect or run each image separately:

```powershell
docker build -t ecommerce-api:1.0 .\backend
docker build -t ecommerce-frontend:1.0 .\frontend
```

Example output (the layer IDs, timings, and final image IDs will differ):

```text
[+] Building ... FINISHED
 => exporting to image
 => => naming to docker.io/library/ecommerce-api:1.0
```

Check which images were created:

```powershell
docker image ls ecommerce-api
docker image ls ecommerce-frontend
```

Example:

```text
REPOSITORY           TAG   IMAGE ID       CREATED          SIZE
ecommerce-api        1.0   0123456789ab   10 seconds ago   200MB
```

The values in output examples are illustrative, not fixed IDs or sizes.

### Why the Dockerfile lines are used

`backend/Dockerfile`:

| Line | Why it is used |
| --- | --- |
| `FROM python:3.12-slim` | Starts from a smaller official Python 3.12 image. |
| `WORKDIR /app` | Sets the working directory for subsequent image commands and the application. |
| `COPY requirements.txt .` | Copies dependency declarations first so Docker can reuse the dependency layer when only application code changes. |
| `RUN pip install --no-cache-dir -r requirements.txt` | Installs Python packages; `--no-cache-dir` avoids keeping pip's download cache in the image. |
| `COPY . .` | Copies the backend source and other build-context files into `/app`, subject to `.dockerignore`. |
| `EXPOSE 8000` | Documents the port the container listens on; it does not publish the port on its own. |
| `HEALTHCHECK ...` | Periodically calls `/health`; Docker uses the result to report whether the backend is healthy. |
| `CMD [...]` | Starts Uvicorn and binds to `0.0.0.0` so the API can be reached from outside the container. |

`frontend/Dockerfile`:

| Line | Why it is used |
| --- | --- |
| `FROM node:22-alpine` | Uses Node.js 22 on a small Alpine Linux base image. |
| `WORKDIR /app` | Sets the frontend working directory inside the image. |
| `COPY package*.json ./` | Copies npm manifests before source files so dependency installation can be cached. |
| `RUN npm ci` | Installs the exact lockfile dependencies reproducibly. |
| `COPY . .` | Copies the frontend code into the image, subject to `.dockerignore`. |
| `RUN npm run build` | Produces the optimized Next.js production build during image creation. |
| `EXPOSE 3000` | Documents the port used by the Next.js server; it does not publish that port by itself. |
| `CMD ["npm","run","start"]` | Starts the production Next.js server when the container runs. |

## 2. Run the complete app with Docker Compose

From the repository root:

```powershell
docker compose up --build
```

`--build` tells Compose to build or rebuild the images before starting the
services. The first run can take longer while dependencies are downloaded.
Leave this terminal open to see container logs.

In another PowerShell window, check container status:

```powershell
docker compose ps
```

Example:

```text
NAME                 SERVICE    STATUS
ecommerce-api        backend    Up (healthy)
ecommerce-frontend   frontend   Up
```

Check the backend health endpoint:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```text
status
------
healthy
```

Open the frontend at `http://localhost:3000`. The backend is published at
`http://localhost:8000`.

Stop the stack with `Ctrl+C` in the Compose terminal, then remove its
containers and default network:

```powershell
docker compose down
```

### Why the Compose lines are used

| Compose setting | Why it is used |
| --- | --- |
| `services` | Declares the containers that make up this application. |
| `backend` / `frontend` | Names the services; Compose also makes service names usable for container-to-container DNS. |
| `build.context` | Selects each app directory as the Docker build context, so its Dockerfile and source are available to the build. |
| `container_name` | Gives the container a predictable name for commands and troubleshooting. |
| `env_file` | Passes runtime variables from the named file into the container. It does not copy that file into the image. |
| `ports` | Maps a host port to a container port (`8000:8000` for the API and `3000:3000` for the web app). |
| `extra_hosts: host.docker.internal:host-gateway` | Makes the host machine address available to the backend container, useful when the database runs on the host instead of in a container. |
| `depends_on` with `condition: service_healthy` | Waits for the backend health check to succeed before starting the frontend. This depends on the backend Dockerfile's `HEALTHCHECK`. |

The Compose service names do not automatically configure every application
URL. In particular, the database hostname in `DB_CONNECTION` must be reachable
from the backend container. Use `host.docker.internal` when the database is
running directly on the Windows host; do not use `localhost` for a host
database from inside the container.

## 3. Build and publish the backend image for Kubernetes

The existing Kubernetes Deployment refers to the image
`mangabhi/ecommerce-backend:1.0`. Build that exact image name from the
repository root:

```powershell
docker build -t mangabhi/ecommerce-backend:1.0 .\backend
```

Authenticate to the image registry, then push the image:

```powershell
docker login
docker push mangabhi/ecommerce-backend:1.0
```

Example push output:

```text
The push refers to repository [docker.io/mangabhi/ecommerce-backend]
1.0: digest: sha256:... size: ...
```

The Kubernetes cluster must be able to pull this image. If you are using a
local cluster such as Minikube instead of a registry, build the image with this
tag in a registry the cluster can access, or load it into that cluster, for
example:

```powershell
minikube image load mangabhi/ecommerce-backend:1.0
```

## 4. Prepare backend configuration for Kubernetes

The backend requires `DB_CONNECTION`, `SECRET_KEY`, `ALGORITHM`, `EXP_TIME`,
and `REFRESH_EXP_TIME`. The current Kubernetes Deployment does not set these
variables, and its Docker image does not include `.env.docker`. Without
configuration, the backend will not start successfully.

For a development cluster, create a Kubernetes Secret from the existing
environment file:

```powershell
kubectl create secret generic backend-config `
  --from-env-file=.\backend\.env.docker `
  --namespace=ecommerce
```

This command requires the namespace to exist first, so run it after step 5's
namespace command. Keep `.env.docker` private and do not commit the generated
Secret values or print them in logs. For production, use your organization's
approved secret-management process.

The Deployment must refer to the Secret for its values to reach the container.
Add the following under the backend container in
`k8s/backend-deployment.yaml`, alongside `image` and `ports`:

```yaml
          envFrom:
            - secretRef:
                name: backend-config
```

`envFrom` imports the Secret's keys as environment variables. The Secret name
must match the `metadata.name` passed to `kubectl create secret`.

The database also has to be reachable from the Kubernetes cluster. A
`localhost` database address means the Pod itself, not the Windows host. Set
`DB_CONNECTION` to an address the cluster can reach before creating the Secret.

## 5. Apply the Kubernetes resources

Create the namespace:

```powershell
kubectl apply -f .\k8s\namespace.yaml
```

Example:

```text
namespace/ecommerce created
```

Now create the Secret as described in step 4 and add the `envFrom` snippet to
the Deployment. Apply the Deployment:

```powershell
kubectl apply -f .\k8s\backend-deployment.yaml
```

Example:

```text
deployment.apps/backend created
```

Wait for the Pod to become ready, then list it:

```powershell
kubectl rollout status deployment/backend --namespace=ecommerce
kubectl get pods --namespace=ecommerce
```

Example:

```text
deployment "backend" successfully rolled out

NAME                       READY   STATUS    RESTARTS   AGE
backend-7c9d8f6b5c-ab123   1/1     Running   0          30s
```

The generated Pod name will differ. If it does not become `Running`, inspect
its events and logs:

```powershell
kubectl describe pods --namespace=ecommerce
kubectl logs deployment/backend --namespace=ecommerce
```

Common causes include an image that the cluster cannot pull, missing backend
environment variables, or a database address that the Pod cannot reach.

### Why the Kubernetes manifest lines are used

`k8s/namespace.yaml`:

| Setting | Why it is used |
| --- | --- |
| `apiVersion: v1` | Selects the Kubernetes core API version used for a Namespace. |
| `kind: Namespace` | Tells Kubernetes to create a namespace resource. |
| `metadata.name: ecommerce` | Gives the namespace its name; namespaced resources are kept under it. |

`k8s/backend-deployment.yaml`:

| Setting | Why it is used |
| --- | --- |
| `apiVersion: apps/v1` | Selects the stable API version for Deployments. |
| `kind: Deployment` | Requests a controller that creates and maintains backend Pods. |
| `metadata.name: backend` | Names the Deployment for commands such as `kubectl rollout status`. |
| `metadata.namespace: ecommerce` | Places the Deployment in the application namespace. |
| `spec.replicas: 1` | Requests one backend Pod. |
| `selector.matchLabels.app: backend` | Tells the Deployment which Pods it owns. It must match the Pod template label. |
| `template.metadata.labels.app: backend` | Labels the Pods so the Deployment selector can find them. |
| `containers.name: backend` | Names the container inside each Pod. |
| `image: mangabhi/ecommerce-backend:1.0` | Identifies the image Kubernetes pulls and runs; it must match the image built and published in step 3. |
| `imagePullPolicy: IfNotPresent` | Reuses a matching image already present on the node; otherwise Kubernetes pulls it. |
| `containerPort: 8000` | Documents the port the container listens on. This does not create a Kubernetes Service or expose it outside the cluster. |
| `resources.requests` | Reserves the CPU and memory Kubernetes uses when scheduling the Pod. |
| `resources.limits` | Caps the container's CPU and memory use. |
| `envFrom.secretRef` (added in step 4) | Supplies the backend's required environment settings from a Kubernetes Secret. |

## 6. Test and clean up Kubernetes resources

The current manifests do not create a Service. For a temporary local test,
forward a local port to the backend Pod:

```powershell
kubectl port-forward deployment/backend 8000:8000 --namespace=ecommerce
```

Keep that command running, then use another PowerShell window:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```text
status
------
healthy
```

Stop port forwarding with `Ctrl+C`. To remove the application resources:

```powershell
kubectl delete -f .\k8s\backend-deployment.yaml
kubectl delete secret backend-config --namespace=ecommerce
kubectl delete -f .\k8s\namespace.yaml
```

Deleting the namespace also deletes namespaced resources such as the Deployment
and Secret. The separate delete commands are shown to make each resource being
removed explicit; if you delete the namespace first, the later namespaced
deletes are unnecessary.

## Quick troubleshooting

- **Compose says an env file is missing:** create the required `.env.docker`
  files before starting the stack.
- **Backend container is unhealthy:** check `docker compose logs backend` and
  confirm the database URL and required environment variables.
- **Kubernetes reports `ImagePullBackOff`:** confirm the image was pushed with
  the exact name and tag in the Deployment, and that the cluster can access the
  registry.
- **Kubernetes reports `CrashLoopBackOff`:** run `kubectl logs
  deployment/backend --namespace=ecommerce`; check the Secret wiring and
  database connectivity.
- **The frontend is not available in Kubernetes:** only the backend
  Deployment is currently defined. Compose runs both apps, but Kubernetes
  needs additional frontend Deployment and Service manifests for a cluster
  frontend.
