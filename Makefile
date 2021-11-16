.PHONY: build serve

serve:
	docker run -u "$(id -u):$(id -g)" -v `pwd`:/app --workdir /app -p 8080:8080 -p 1024:1024 balthek/zola:0.14.0 serve --interface 0.0.0.0 --port 8080 --base-url localhost

build:
	docker run -u "$(id -u):$(id -g)" -v `pwd`:/app --workdir /app balthek/zola:0.14.0 build

push:
	git pull origin master; \
	git add --all; \
	git commit --m "automated push"; \
	git push origin master
