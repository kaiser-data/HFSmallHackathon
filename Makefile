# DAYDREAM — deploy + COST CONTROL surface.
#
# The golden rule after the $200 incident: GPU apps are ALWAYS deployed
# scale-to-zero (min_containers=0, max_containers=1). They cost nothing idle and
# cannot be left running. "Warm for a demo" is a time-boxed LEASE driven by the
# cloud guardian — forget to tear down and it expires on its own, laptop or not.
#
#   make status      what's running + lease state   (run this whenever unsure)
#   make stop        PANIC BUTTON — stop every app now
#   make deploy      (re)deploy all endpoints scale-to-zero (safe, $0/hr idle)
#   make demo-up     lease a 30-min warm window for a live demo
#   make demo-down   end the lease now (GPUs scale to zero within ~5 min)
#
# Cost lives in the ACTIVE Modal workspace — check it with `make whoami`.

# Activate venv AND load .env (so MODAL_WORKSPACE is exported for the guardian
# deploy, which bakes it into its image to derive endpoint URLs).
PY := . .venv/bin/activate && set -a && [ -f .env ] && . ./.env ; set +a ;
APPS := small-hack-vllm small-hack-llamacpp small-hack-flux
LEASE_MIN ?= 30
LEASE_APPS ?= vllm,llamacpp,flux

.PHONY: whoami status stop deploy deploy-guardian demo-up demo-down

whoami:
	@$(PY) echo "Modal workspace: $$(modal profile current)"

status:
	@$(PY) echo "=== Modal workspace: $$(modal profile current) ===" ; \
	  modal app list 2>/dev/null | grep -iE "small-hack|App ID" || true ; \
	  echo "=== warm lease ===" ; \
	  modal run modal_app/guardian.py::lease_status 2>/dev/null || echo "(guardian not deployed)"

# PANIC BUTTON: clear the lease AND stop every app. Use any time spend looks wrong.
stop:
	@$(PY) modal run modal_app/guardian.py::lease_clear 2>/dev/null || true ; \
	  for a in $(APPS) ; do echo "stopping $$a" ; modal app stop $$a -y 2>/dev/null || true ; done ; \
	  echo "ALL STOPPED — \$$0/hr."

# Deploy everything scale-to-zero + the always-on guardian. Safe to leave
# deployed: GPU idle cost is $0, the guardian is a cheap CPU cron.
deploy: deploy-guardian
	@$(PY) modal deploy modal_app/vllm_server.py ; \
	  modal deploy modal_app/llamacpp_server.py ; \
	  modal deploy modal_app/flux_server.py

# The guardian bakes $MODAL_WORKSPACE into its image to derive endpoint URLs.
deploy-guardian:
	@$(PY) test -n "$$MODAL_WORKSPACE" || { echo "ERROR: set MODAL_WORKSPACE in .env first"; exit 1; } ; \
	  echo "deploying guardian for workspace: $$MODAL_WORKSPACE" ; \
	  modal deploy modal_app/guardian.py

# Lease a warm window for a live demo. Auto-expires — this is the safety net.
demo-up:
	@$(PY) modal run modal_app/guardian.py::lease_set --minutes $(LEASE_MIN) --apps $(LEASE_APPS)

demo-down:
	@$(PY) modal run modal_app/guardian.py::lease_clear
