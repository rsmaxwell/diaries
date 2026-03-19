#!/bin/bash
set -euo pipefail
set -x

BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd "$BASEDIR" && pwd)
PROJECT_DIR=$(dirname "$SCRIPT_DIR")
BUILD_DIR="${PROJECT_DIR}/build"

. "${BUILD_DIR}/buildinfo"

cd "${PROJECT_DIR}"

# ----------------------------
# Image naming
# ----------------------------

# Override from Jenkins env if desired
IMAGE_REGISTRY="${IMAGE_REGISTRY:-docker.io}"
IMAGE_NAMESPACE="${IMAGE_NAMESPACE}"
IMAGE_NAME="${IMAGE_NAME:-diaries-responder}"

if [ -n "${IMAGE_NAMESPACE}" ]; then
  IMAGE_REPO="${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_NAME}"
else
  IMAGE_REPO="${IMAGE_REGISTRY}/${IMAGE_NAME}"
fi

IMAGE_TAG="${VERSION}"

# Optional convenience tags
EXTRA_TAGS=()

case "${REPOSITORY}" in
  releases)
    EXTRA_TAGS+=("latest")
    ;;
  integration)
    EXTRA_TAGS+=("integration")
    ;;
  snapshots)
    EXTRA_TAGS+=("snapshot")
    ;;
esac

echo "PROJECT_DIR=${PROJECT_DIR}"
echo "BUILD_DIR=${BUILD_DIR}"
echo "VERSION=${VERSION}"
echo "REPOSITORY=${REPOSITORY}"
echo "IMAGE_REPO=${IMAGE_REPO}"
echo "IMAGE_TAG=${IMAGE_TAG}"

# ----------------------------
# Preconditions
# ----------------------------

if [ ! -f "${PROJECT_DIR}/Dockerfile" ]; then
  echo "ERROR: Dockerfile not found at ${PROJECT_DIR}/Dockerfile" >&2
  exit 1
fi

# Optional: if your Dockerfile copies a packaged distribution built earlier
# then make sure it exists before building the image.
# Adjust this check to match your actual artifact path.
if [ ! -d "${PROJECT_DIR}/diaries-responder/build" ] && [ ! -f "${PROJECT_DIR}/diaries-responder/build/libs/diaries-responder.jar" ]; then
  echo "WARNING: expected responder build output not found yet."
  echo "Make sure the package/build stage runs before image.sh if the Dockerfile depends on built artifacts."
fi

# ----------------------------
# Build
# ----------------------------

docker build \
  --pull \
  --tag "${IMAGE_REPO}:${IMAGE_TAG}" \
  --build-arg VERSION="${VERSION}" \
  --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --build-arg VCS_REF="${GIT_COMMIT:-unknown}" \
  "${PROJECT_DIR}"

for tag in "${EXTRA_TAGS[@]}"; do
  docker tag "${IMAGE_REPO}:${IMAGE_TAG}" "${IMAGE_REPO}:${tag}"
done

# ----------------------------
# Write image info for later stages
# ----------------------------

cat > "${BUILD_DIR}/imageinfo" <<EOF
IMAGE_REPO="${IMAGE_REPO}"
IMAGE_TAG="${IMAGE_TAG}"
IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"
EOF

echo "imageinfo:"
cat "${BUILD_DIR}/imageinfo"

# ----------------------------
# Optional push
# ----------------------------

if [ "${PUSH_IMAGE:-false}" = "true" ]; then
  : "${IMAGE_REGISTRY:?IMAGE_REGISTRY not set}"
  : "${DOCKER_USERNAME:?DOCKER_USERNAME not set}"
  : "${DOCKER_PASSWORD:?DOCKER_PASSWORD not set}"

  echo "${DOCKER_PASSWORD}" | docker login "${IMAGE_REGISTRY}" \
    --username "${DOCKER_USERNAME}" \
    --password-stdin
fi

if [ "${PUSH_IMAGE:-false}" = "true" ]; then
  docker push "${IMAGE_REPO}:${IMAGE_TAG}"
  for tag in "${EXTRA_TAGS[@]}"; do
    docker push "${IMAGE_REPO}:${tag}"
  done
fi