#!/usr/bin/env sh
set -eu

if curl -sf "${E2E_BASE_URL}/health/ready" >/dev/null; then
  echo "Using running API at ${E2E_BASE_URL}"
  E2E_BASE_URL="${E2E_BASE_URL}" ${UV_RUN} pytest ${PYTEST_FLAGS} ${ALL_TEST_ARGS:-}
  exit 0
fi

if [ "${E2E_BASE_URL}" != "${LOCAL_E2E_BASE_URL}" ]; then
  echo "API unreachable at ${E2E_BASE_URL}. Auto-start is only supported for ${LOCAL_E2E_BASE_URL}."
  exit 1
fi

echo "Starting local API for all tests..."
${UV_RUN} python -m uvicorn app.main:app --host "${APP_HOST}" --port "${APP_PORT}" >/tmp/personal-finance-api-test-all.log 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "${SERVER_PID}" >/dev/null 2>&1 || true
  wait "${SERVER_PID}" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

i=0
while [ "${i}" -lt 60 ]; do
  if curl -sf "${E2E_BASE_URL}/health/ready" >/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.5
done

if ! curl -sf "${E2E_BASE_URL}/health/ready" >/dev/null; then
  echo "Local API did not become ready in time."
  exit 1
fi

E2E_BASE_URL="${E2E_BASE_URL}" ${UV_RUN} pytest ${PYTEST_FLAGS} ${ALL_TEST_ARGS:-}
