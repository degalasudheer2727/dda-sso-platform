.PHONY: bootstrap up status stop validate images export backup render
bootstrap:
	python3 scripts/bootstrap.py
up:
	scripts/local.sh up -d
status:
	scripts/local.sh ps
stop:
	scripts/local.sh stop
validate:
	python3 -m py_compile scripts/*.py
	python3 scripts/verify-manifests.py openshift/reference
	kubectl kustomize openshift/reference > /dev/null
images:
	docker build -t dda/dex:v2.45.1 -f dex/Dockerfile .
	docker build -t dda/keycloak:26.7.3 -f keycloak/Dockerfile .
	docker build -t dda/open-webui:v0.11.3 -f open-webui/Dockerfile .
export: images
	scripts/export-images.sh
backup:
	scripts/backup-local.sh
render:
	@test -n "$(DOMAIN)" -a -n "$(REGISTRY)" || (echo 'Set DOMAIN and REGISTRY'; exit 1)
	python3 scripts/render-openshift.py --domain "$(DOMAIN)" --registry "$(REGISTRY)" $(RENDER_ARGS)
