.PHONY: build serve

serve:
	docker run -u `id -u`:`id -g` -v `pwd`:/app --workdir /app -p 3333:3333 ghcr.io/getzola/zola:v0.15.1 serve --interface 0.0.0.0 --port 3333 --base-url localhost

build:
	docker run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app ghcr.io/getzola/zola:v0.15.1 build

push:
	git pull origin master; \
	git add --all; \
	git commit --m "automated push"; \
	git push origin master
